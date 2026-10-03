"""Kaggle Benchmark Task: Loglan Predicate Slot Identification (Zero-Shot vs RAG).

Official task definitions using the kaggle-benchmarks library.
Compares LLMs on formal argument slot extraction with and without dictionary RAG.
"""

import kaggle_benchmarks as kbench
import pandas as pd
import requests

# 1. Fetch benchmark dataset directly from GitHub
DATASET_URL = "https://raw.githubusercontent.com/torrua/loglan-bench/main/data/benchmark_dataset.json"
response = requests.get(DATASET_URL)
data = response.json()

slot_cases = [c for c in data["cases"] if c["category"] == "slot_identification"]

# 2. Fetch LOD dictionary context for RAG
RAG_URL = "https://raw.githubusercontent.com/torrua/loglan-bench/main/data/rag_context.json"
try:
    rag_data = requests.get(RAG_URL).json()
    rag_defs = {
        word: info["definitions"][0]["body"]
        for word, info in rag_data.get("definitions", {}).items()
        if info.get("definitions")
    }
except Exception:
    rag_defs = {}

# 3. Build task evaluation DataFrame
df = pd.DataFrame([
    {
        "predicate": c["predicate"],
        "sentence": c["sentence"],
        "lod_definition": rag_defs.get(c["predicate"], c.get("definition_slots", "Loglan predicate")),
        "expected_donor": list(c["expected_slots"].values())[0].split()[0]  # Expected x1 entity
    }
    for c in slot_cases
])


# 4. Zero-Shot Task: Model must know Loglan argument slots from pretraining
@kbench.task(name="loglan_predicate_slots_zeroshot")
def eval_loglan_slots_zeroshot(llm, predicate: str, sentence: str, expected_donor: str) -> bool:
    """Zero-shot slot identification without dictionary context."""
    prompt = (
        f"In the Loglan formal language, predicates have strict argument positions.\n"
        f"For the predicate '{predicate}' in the sentence: '{sentence}',\n"
        f"which entity fills slot x1 (the agent/donor/subject)?\n"
        f"State the exact entity name."
    )
    response = llm.prompt(prompt)
    return expected_donor.lower() in response.lower()


# 5. RAG Task: Model receives the official LOD dictionary slot template
@kbench.task(name="loglan_predicate_slots_rag")
def eval_loglan_slots_rag(llm, predicate: str, sentence: str, lod_definition: str, expected_donor: str) -> bool:
    """RAG-augmented slot identification with LOD dictionary context."""
    prompt = (
        f"You are an expert in the Loglan artificial language.\n"
        f"Official dictionary definition for predicate '{predicate}':\n"
        f"\"{lod_definition}\"\n\n"
        f"In the sentence: '{sentence}',\n"
        f"which entity fills slot x1 according to the definition above?\n"
        f"State the exact entity name."
    )
    response = llm.prompt(prompt)
    return expected_donor.lower() in response.lower()


if __name__ == "__main__":
    print(f"Loaded {len(df)} Loglan slot cases.")
    print("Sample case:")
    print(df.iloc[0][["predicate", "sentence", "lod_definition", "expected_donor"]])
