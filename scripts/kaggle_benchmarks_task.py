"""Kaggle Benchmark Task: Loglan Predicate Slot Identification.

Official task definition using the kaggle-benchmarks library.
Evaluates LLMs on formal argument slot extraction.
"""

import kaggle_benchmarks as kbench
import pandas as pd
import requests

# 1. Fetch benchmark dataset directly from GitHub
DATASET_URL = "https://raw.githubusercontent.com/torrua/loglan-bench/main/data/benchmark_dataset.json"
response = requests.get(DATASET_URL)
data = response.json()

slot_cases = [c for c in data["cases"] if c["category"] == "slot_identification"]

# 2. Build task evaluation DataFrame
df = pd.DataFrame([
    {
        "predicate": c["predicate"],
        "sentence": c["sentence"],
        "expected_donor": list(c["expected_slots"].values())[0].split()[0]  # Expected x1 entity
    }
    for c in slot_cases
])


# 3. Define the official Kaggle Benchmark Task
@kbench.task(name="loglan_predicate_slots")
def eval_loglan_slots(llm, predicate: str, sentence: str, expected_donor: str) -> bool:
    """Evaluates whether the model correctly maps argument slots in Loglan without ambiguity."""
    prompt = (
        f"In the Loglan formal language, predicates have strict argument positions.\n"
        f"For the predicate '{predicate}' in the sentence: '{sentence}',\n"
        f"which entity fills slot x1 (the agent/donor/subject)?\n"
        f"State the exact entity name."
    )
    response = llm.prompt(prompt)
    return expected_donor.lower() in response.lower()


# 4. Execute evaluation across available Kaggle LLMs
print(f"Evaluating {len(df)} Loglan predicate slot cases...")
runs = eval_loglan_slots.evaluate(
    llm=[kbench.llm],
    evaluation_data=df
)

# 5. Output benchmark results
results_df = runs.as_dataframe()
accuracy = results_df["result"].mean()
print(f"Loglan Predicate Slot Accuracy: {accuracy * 100:.1f}%")
