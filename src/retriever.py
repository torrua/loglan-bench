"""Two-tier context retriever for Loglan: LOD Dictionary + Grammar Documents."""

import re
import sqlite3
from typing import Dict, List, Any

try:
    from src.config import DB_PATH, DEFAULT_TOP_WORDS, DEFAULT_TOP_DOCS
except ImportError:
    from config import DB_PATH, DEFAULT_TOP_WORDS, DEFAULT_TOP_DOCS


def sanitize_fts_query(query: str) -> str:
    """Sanitize query for SQLite FTS5 matching, removing special characters."""
    # Remove FTS5 special characters like * " - ^ : ( )
    cleaned = re.sub(r'[*"+\-^:()~{}]', ' ', query)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
    if not tokens:
        return '""'
    # Use OR across tokens or exact prefix
    return " OR ".join(f'"{token}"' for token in tokens)


class LoglanRetriever:
    """Retrieves grounded linguistic context from SQLite LOD & Grammar documents."""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = str(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search_dictionary(self, query: str, limit: int = DEFAULT_TOP_WORDS) -> List[Dict[str, Any]]:
        """Search words and definitions in LOD dictionary."""
        results = []
        conn = self._get_connection()
        try:
            fts_query = sanitize_fts_query(query)

            # 1. Try exact word match first
            exact_word = query.strip().split()[0] if query.strip() else ""
            exact_rows = conn.execute("""
                SELECT w.id, w.name, w.type, d.body, d.usage, d.grammar_code, d.slots, d.notes
                FROM words w
                JOIN definitions d ON d.word_id = w.id
                WHERE LOWER(w.name) = LOWER(?)
                LIMIT ?
            """, (exact_word, limit)).fetchall()

            seen_ids = set()
            for r in exact_rows:
                seen_ids.add(r["id"])
                results.append(dict(r))

            # 2. Try FTS5 over definitions
            if len(results) < limit and fts_query != '""':
                try:
                    fts_rows = conn.execute("""
                        SELECT w.id, w.name, w.type, d.body, d.usage, d.grammar_code, d.slots, d.notes,
                               rank
                        FROM def_fts f
                        JOIN definitions d ON d.id = f.rowid
                        JOIN words w ON w.id = d.word_id
                        WHERE def_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """, (fts_query, limit - len(results))).fetchall()

                    for r in fts_rows:
                        if r["id"] not in seen_ids:
                            seen_ids.add(r["id"])
                            results.append(dict(r))
                except sqlite3.OperationalError:
                    pass

            # 3. Fallback: LIKE substring match on word name and definition body
            if len(results) < limit:
                like_term = f"%{query.strip()}%"
                like_rows = conn.execute("""
                    SELECT w.id, w.name, w.type, d.body, d.usage, d.grammar_code, d.slots, d.notes
                    FROM words w
                    JOIN definitions d ON d.word_id = w.id
                    WHERE (w.name LIKE ? OR d.body LIKE ?)
                    LIMIT ?
                """, (like_term, like_term, limit - len(results))).fetchall()

                for r in like_rows:
                    if r["id"] not in seen_ids:
                        seen_ids.add(r["id"])
                        results.append(dict(r))

            # Fetch complex affix connections for any complex words found
            for item in results:
                child_words = conn.execute("""
                    SELECT w.name, w.type FROM connect_words c
                    JOIN words w ON w.id = c.child_id
                    WHERE c.parent_id = ?
                """, (item["id"],)).fetchall()
                if child_words:
                    item["components"] = [f"{cw['name']} ({cw['type']})" for cw in child_words]

        finally:
            conn.close()

        return results

    def search_grammar_docs(self, query: str, limit: int = DEFAULT_TOP_DOCS) -> List[Dict[str, Any]]:
        """Search scraped grammar textbook chapters and papers."""
        results = []
        conn = self._get_connection()
        try:
            fts_query = sanitize_fts_query(query)

            # 1. Try FTS5 over documents
            if fts_query != '""':
                try:
                    rows = conn.execute("""
                        SELECT d.title, d.source_url, d.chunk, rank
                        FROM doc_fts f
                        JOIN documents d ON d.id = f.rowid
                        WHERE doc_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """, (fts_query, limit)).fetchall()
                    for r in rows:
                        results.append(dict(r))
                except sqlite3.OperationalError:
                    pass

            # 2. Fallback to LIKE if FTS yielded few results
            if len(results) < limit:
                {r["source_url"] for r in results}
                like_term = f"%{query.strip()}%"
                like_rows = conn.execute("""
                    SELECT title, source_url, chunk
                    FROM documents
                    WHERE (chunk LIKE ? OR title LIKE ?)
                    LIMIT ?
                """, (like_term, like_term, limit - len(results))).fetchall()

                for r in like_rows:
                    results.append(dict(r))

        finally:
            conn.close()

        return results

    def retrieve_context(
        self,
        query: str,
        top_words: int = DEFAULT_TOP_WORDS,
        top_docs: int = DEFAULT_TOP_DOCS
    ) -> str:
        """Combine dictionary and document retrieval into a structured context prompt."""
        dict_results = self.search_dictionary(query, limit=top_words)
        doc_results = self.search_grammar_docs(query, limit=top_docs)

        sections: List[str] = []

        # 1. Format Dictionary entries
        if dict_results:
            dict_lines = []
            for item in dict_results:
                name = item.get("name", "")
                wtype = item.get("type", "Word")
                slots = item.get("slots") or ""
                code = item.get("grammar_code") or ""
                grammar_str = f" [{slots}{code}]" if (slots or code) else ""
                body = item.get("body", "").strip()
                usage = item.get("usage")

                line = f"- **{name}** ({wtype}){grammar_str}: {body}"
                if usage:
                    line += f"\n  *Usage*: {usage}"
                if "components" in item and item["components"]:
                    line += f"\n  *Derived from*: {', '.join(item['components'])}"
                dict_lines.append(line)

            sections.append("### LOD Dictionary Context\n" + "\n\n".join(dict_lines))

        # 2. Format Grammar documents
        if doc_results:
            doc_lines = []
            for doc in doc_results:
                title = doc.get("title", "Grammar Lesson")
                url = doc.get("source_url", "")
                chunk = doc.get("chunk", "").strip()
                # Truncate overly long chunks for prompt efficiency
                if len(chunk) > 1200:
                    chunk = chunk[:1200] + "... [truncated]"
                doc_lines.append(f"#### Reference: {title} ({url})\n{chunk}")

            sections.append("### Loglan Grammar References\n" + "\n\n".join(doc_lines))

        if not sections:
            return "No specific dictionary or grammar matches found in the LOD corpus."

        return "\n\n---\n\n".join(sections)


def retrieve_context(query: str, db_path: str = str(DB_PATH), top_k: int = 5) -> str:
    """Convenience function matching specification signature."""
    retriever = LoglanRetriever(db_path=db_path)
    return retriever.retrieve_context(query, top_words=top_k, top_docs=3)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    test_q = sys.argv[1] if len(sys.argv) > 1 else "donsu"
    print(f"Testing retrieval for query: '{test_q}'\n")
    print(retrieve_context(test_q))
