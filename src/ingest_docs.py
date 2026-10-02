"""Ingest Loglan grammar articles from loglan.org into SQLite with FTS5 search."""

import re
import sqlite3
import sys
import urllib.request
import urllib.error
from typing import List, Tuple
from bs4 import BeautifulSoup

try:
    from src.config import DB_PATH, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS
except ImportError:
    from config import DB_PATH, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS

# Core reference articles from loglan.org
GRAMMAR_SOURCES: List[Tuple[str, str]] = [
    (
        "Easy Loglan Introduction",
        "https://www.loglan.org/Articles/easy-loglan-introduction.html"
    ),
    (
        "Easy Loglan Description",
        "https://www.loglan.org/Articles/easy-loglan-description.html"
    ),
    (
        "Case Tag Theory & Predicate Roles",
        "https://www.loglan.org/Articles/case-tag-theory.html"
    ),
    (
        "Complex Word Making & Affixes",
        "https://www.loglan.org/Articles/complex-making.html"
    ),
    (
        "The Faces of Gu (Particle Disambiguation)",
        "https://www.loglan.org/Articles/faces-of-gu.html"
    ),
    (
        "Logic and Economy in Loglan Syntax",
        "https://www.loglan.org/Articles/logic-and-economy.html"
    ),
    (
        "Sets and Masses in Loglan",
        "https://www.loglan.org/Articles/sets-and-masses.html"
    ),
    (
        "Sets and Multiples",
        "https://www.loglan.org/Articles/sets-and-multiples.html"
    ),
    (
        "Clarity and Unambiguity in Predicate Logic",
        "https://www.loglan.org/Articles/clarity-abstract.html"
    ),
]


def fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch URL content with custom User-Agent."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "LoglanBenchBot/1.0 (+https://github.com/torrua/loglan-bench)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def clean_html_to_paragraphs(html_text: str) -> List[str]:
    """Parse HTML and extract meaningful textual paragraphs."""
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove script, style, navigation elements
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    paragraphs = []
    # Collect text from headings, paragraphs, list items, and blockquotes
    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre"]):
        text = element.get_text(separator=" ", strip=True)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 20:  # Skip tiny fragments
            paragraphs.append(text)

    # Fallback to full text split if specific tags yielded very few items
    if not paragraphs:
        raw_text = soup.get_text(separator="\n", strip=True)
        paragraphs = [p.strip() for p in raw_text.split("\n") if len(p.strip()) > 20]

    return paragraphs


def chunk_paragraphs(
    paragraphs: List[str],
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS
) -> List[str]:
    """Combine paragraphs into overlapping chunks of approx chunk_size words."""
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_word_count = 0

    for para in paragraphs:
        words = para.split()
        word_count = len(words)

        if current_word_count + word_count > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            # Keep the last paragraph for overlap context if available
            if overlap > 0 and len(current_chunk) > 1:
                current_chunk = [current_chunk[-1]]
                current_word_count = len(current_chunk[0].split())
            else:
                current_chunk = []
                current_word_count = 0

        current_chunk.append(para)
        current_word_count += word_count

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def setup_schema(conn: sqlite3.Connection):
    """Create documents table and FTS5 virtual tables."""
    cursor = conn.cursor()

    # Documents storage table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            chunk TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_url, chunk_index)
        );
    """)

    # FTS5 for grammar documents
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS doc_fts USING fts5(
            chunk, title,
            content='documents',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 1'
        );
    """)

    # FTS5 for dictionary definitions if definitions table exists
    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "definitions" in tables:
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS def_fts USING fts5(
                body, usage, notes,
                content='definitions',
                content_rowid='id',
                tokenize='unicode61 remove_diacritics 1'
            );
        """)

    conn.commit()


def ingest_all(db_path: str = str(DB_PATH)):
    """Scrape and index all target sources into SQLite."""
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)

    print("Setting up schemas and FTS5 virtual tables...")
    setup_schema(conn)

    total_chunks = 0
    for title, url in GRAMMAR_SOURCES:
        print(f"\nProcessing '{title}' ({url})...")
        try:
            html = fetch_url(url)
            paragraphs = clean_html_to_paragraphs(html)
            chunks = chunk_paragraphs(paragraphs)
            print(f" -> Extracted {len(paragraphs)} paragraphs, generated {len(chunks)} chunks.")

            for idx, chunk in enumerate(chunks):
                conn.execute("""
                    INSERT INTO documents (title, source_url, chunk, chunk_index)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(source_url, chunk_index) DO UPDATE SET
                        title = excluded.title,
                        chunk = excluded.chunk;
                """, (title, url, chunk, idx))
                total_chunks += 1

        except Exception as e:
            print(f" [Warning] Failed to fetch {url}: {e}", file=sys.stderr)

    conn.commit()

    print("\nRebuilding FTS5 indexes for documents and definitions...")
    try:
        conn.execute("INSERT INTO doc_fts(doc_fts) VALUES('rebuild');")
        conn.execute("INSERT INTO def_fts(def_fts) VALUES('rebuild');")
        conn.commit()
        print("FTS5 indexes rebuilt successfully.")
    except Exception as e:
        print(f"FTS5 rebuild notice: {e}")

    # Summary verification
    doc_count = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
    fts_count = conn.execute("SELECT count(*) FROM doc_fts").fetchone()[0]
    def_fts_count = conn.execute("SELECT count(*) FROM def_fts").fetchone()[0]

    print("\n=== Ingestion Summary ===")
    print(f"Documents in storage: {doc_count}")
    print(f"Entries in doc_fts:   {fts_count}")
    print(f"Entries in def_fts:   {def_fts_count}")
    conn.close()


if __name__ == "__main__":
    target_db = sys.argv[1] if len(sys.argv) > 1 else str(DB_PATH)
    ingest_all(target_db)
