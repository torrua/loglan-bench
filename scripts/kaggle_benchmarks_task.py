"""Kaggle Benchmark Task: Loglan Predicate Slot Identification (Zero-Shot vs RAG).

Official task definitions using the kaggle-benchmarks library.
Compares LLMs on formal argument slot extraction with and without dictionary RAG.
Features robust word-boundary regex verification to eliminate substring false-positives.
"""

import re
import kaggle_benchmarks as kbench
import pandas as pd
import requests

# 1. Fetch benchmark dataset and dictionary
DATASET_URL = "https://raw.githubusercontent.com/torrua/loglan-bench/main/data/benchmark_dataset.json"
RAG_URL = "https://raw.githubusercontent.com/torrua/loglan-bench/main/data/rag_context.json"

cases = requests.get(DATASET_URL).json()["cases"]
slot_cases = [c for c in cases if c.get("category") == "slot_identification"]

try:
    rag_data = requests.get(RAG_URL).json()
    rag_defs = {
        word: info["definitions"][0]["body"]
        for word, info in rag_data.get("definitions", {}).items()
        if info.get("definitions")
    }
except Exception:
    rag_defs = {}

# 2. Build clean evaluation DataFrame with exact word-boundary regex targets
rows = []
for c in slot_cases:
    exp_raw = list(c["expected_slots"].values())[0]
    entity = re.split(r"\s*\(", exp_raw)[0].strip()
    words = entity.split()
    
    # If entity has article ('La Djan', 'Le trime'), allow full phrase or core noun
    if len(words) > 1 and words[0].lower() in ["la", "le", "li", "lo"]:
        aliases = [entity.lower(), words[-1].lower()]
    else:
        aliases = [entity.lower()]
    
    target_pattern = r"\b(" + "|".join(re.escape(a) for a in aliases) + r")\b"
    lod_def = rag_defs.get(c["predicate"], c.get("definition_slots", "Loglan predicate"))

    rows.append({
        "case_id": c["id"],
        "predicate": c["predicate"],
        "sentence": c["sentence"],
        "lod_definition": lod_def,
        "expected_entity": entity,
        "target_pattern": target_pattern
    })

df = pd.DataFrame(rows)


# 3. Define Zero-Shot Task (No Dictionary Context)
@kbench.task(name="loglan_slot_zeroshot")
def eval_loglan_slot_zeroshot(llm, predicate: str, sentence: str, target_pattern: str) -> bool:
    """Zero-shot Loglan argument slot extraction without dictionary context."""
    prompt = (
        f"Task: Identify the Loglan argument slot x1.\n\n"
        f"Sentence: \"{sentence}\"\n"
        f"Predicate: \"{predicate}\"\n\n"
        f"Question: Which entity in the sentence fills slot x1 (the subject / agent)?\n"
        f"Answer with only the exact entity name:"
    )
    response = llm.prompt(prompt)
    if not response or not isinstance(response, str):
        return False
    return bool(re.search(target_pattern, response, re.IGNORECASE))


# 4. Define RAG Task (With LOD Dictionary Context)
@kbench.task(name="loglan_slot_rag")
def eval_loglan_slot_rag(llm, predicate: str, sentence: str, lod_definition: str, target_pattern: str) -> bool:
    """RAG-augmented Loglan argument slot extraction with LOD dictionary context."""
    prompt = (
        f"Task: Identify the Loglan argument slot x1 using the dictionary definition.\n\n"
        f"Sentence: \"{sentence}\"\n"
        f"Predicate: \"{predicate}\"\n"
        f"Dictionary Definition: \"{lod_definition}\"\n\n"
        f"Question: According to the definition, which entity in the sentence fills slot x1?\n"
        f"Answer with only the exact entity name:"
    )
    response = llm.prompt(prompt)
    if not response or not isinstance(response, str):
        return False
    return bool(re.search(target_pattern, response, re.IGNORECASE))


if __name__ == "__main__":
    print(f"Loaded {len(df)} slot cases with strict word-boundary verification.")
    for _, row in df.head(3).iterrows():
        print(f"Case {row['case_id']}: {row['predicate']} | entity='{row['expected_entity']}' | pattern={row['target_pattern']}")
