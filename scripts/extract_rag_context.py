"""Extract LOD definitions for benchmark cases into a compact RAG context JSON."""
import json
import sqlite3

DB_PATH = "data/export.db"
DATASET_PATH = "data/benchmark_dataset.json"
OUTPUT_PATH = "data/rag_context.json"

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    bench = json.load(f)

# Collect all Loglan words from benchmark cases
all_words = set()
for case in bench["cases"]:
    pred = case.get("predicate", "")
    if pred:
        all_words.add(pred.lower())
    for field in ["loglan", "sentence"]:
        text = case.get(field, "")
        if text:
            for w in text.split():
                cleaned = w.strip(",.!?()[]{}\"'").lower()
                if len(cleaned) >= 3 and cleaned.isalpha():
                    all_words.add(cleaned)
    for var in case.get("loglan_variants", []):
        for w in var.get("phrase", "").split():
            cleaned = w.strip(",.!?()[]{}\"'").lower()
            if len(cleaned) >= 3 and cleaned.isalpha():
                all_words.add(cleaned)
    for slot_val in case.get("expected_slots", {}).values():
        for w in slot_val.split():
            cleaned = w.strip(",.!?()[]{}\"'").lower()
            if len(cleaned) >= 3 and cleaned.isalpha():
                all_words.add(cleaned)

print(f"Found {len(all_words)} unique Loglan words in benchmark")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get type mapping
c.execute("SELECT id, type, type_x, description FROM types")
type_map = {row[0]: {"type": row[1], "type_x": row[2], "desc": row[3]} for row in c.fetchall()}

definitions = {}
for word in sorted(all_words):
    c.execute("""
        SELECT w.id, w.name, w.type, w.origin,
               d.body, d.usage, d.slots, d.case_tags, d.grammar_code, d.notes
        FROM words w
        LEFT JOIN definitions d ON d.word_id = w.id
        WHERE w.name = ? COLLATE NOCASE
    """, (word,))
    rows = c.fetchall()
    if rows:
        entry = {
            "word": rows[0][1],
            "type": type_map.get(rows[0][2], {}).get("type_x", ""),
            "origin": rows[0][3],
            "definitions": []
        }
        for row in rows:
            if row[4]:  # has definition body
                defn = {"body": row[4]}
                if row[5]: defn["usage"] = row[5]
                if row[6]: defn["slots"] = row[6]
                if row[7]: defn["case_tags"] = row[7]
                if row[8]: defn["grammar"] = row[8]
                if row[9]: defn["notes"] = row[9]
                entry["definitions"].append(defn)
        definitions[word] = entry

print(f"Matched {len(definitions)} words with definitions")

# Get key grammar documents (just titles and first chunks)
c.execute("""
    SELECT title, chunk FROM documents
    WHERE title LIKE '%particle%' OR title LIKE '%case tag%'
       OR title LIKE '%Faces of Gu%' OR title LIKE '%grouping%'
       OR title LIKE '%modifier%' OR title LIKE '%predicate%'
    ORDER BY title, chunk_index
    LIMIT 20
""")
grammar_docs = []
for row in c.fetchall():
    grammar_docs.append({"title": row[0], "text": row[1][:500]})

# Essential grammar rules (compact reference)
grammar_rules = {
    "ge_particle": "The particle 'ge' forces right-grouping of modifiers. Default is left-to-right. 'le bilti cmalo nirli ckela' = (((bilti cmalo) nirli) ckela). 'le bilti ge cmalo nirli ckela' = (bilti (cmalo (nirli ckela))). 'ge' opens a scope extending to end of modifier string.",
    "ke_gu_particles": "'ke' opens explicit parenthesization, 'gu' closes it. 'le ke bilti cmalo gu nirli ckela' = ((bilti cmalo) (nirli ckela)). Like mathematical brackets in speech.",
    "ce_particle": "'ce' conjoins modifiers at same scope: 'bilti ce cmalo' = 'both pretty and little'. 'le bilti ce cmalo nirli ckela' = school of girls who are both pretty and little.",
    "case_tags": "Case tags mark argument roles: 'kao' (actor x1), 'dio' (recipient x3), 'beu' (patient x2), 'liu' (instrument x4). Allow free word order with unambiguous role assignment.",
    "zero_ambiguity": "Every valid Loglan sentence has exactly ONE parse tree. No dangling modifiers, no ambiguous PP-attachment. Enforced by grouping particles and case tags.",
    "predicate_slots": "Loglan predicates have numbered argument slots: x1 (agent), x2 (patient), x3 (recipient/goal), x4 (instrument/source), x5 (additional). The LOD defines exact slot structure per predicate.",
    "complex_words": "Loglan complex words (borrowings/compounds) are built from primitives via affixes. E.g. 'cinkau' = 'cinta' (infant) + 'kangu' (dog) = puppy. 'sorme' = sister (primitive).",
    "little_words": "Little words are grammatical particles: 'le' (the), 'la' (name marker), 'pa' (past tense), 'nu' (argument reversal), 'leda' (his/her, possessive)."
}

# Build output
rag_context = {
    "metadata": {
        "description": "Compact RAG context for the 60-case Loglan benchmark. Contains LOD definitions for all referenced words and essential Loglan grammar rules.",
        "total_definitions": len(definitions),
        "grammar_rules": len(grammar_rules),
        "grammar_documents": len(grammar_docs)
    },
    "definitions": definitions,
    "grammar_rules": grammar_rules,
    "grammar_documents": grammar_docs
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(rag_context, f, indent=2, ensure_ascii=False, default=str)

import os
file_size = os.path.getsize(OUTPUT_PATH)
print(f"\nSaved to {OUTPUT_PATH}")
print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

# Print sample
sample_word = "donsu"
if sample_word in definitions:
    print(f"\nSample - {sample_word}:")
    for d in definitions[sample_word]["definitions"]:
        print(f"  {d['body']}")
        if "case_tags" in d:
            print(f"  Case tags: {d['case_tags']}")
        if "slots" in d:
            print(f"  Slots: {d['slots']}")

conn.close()
