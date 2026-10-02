"""Kaggle Benchmarks Integration Task for Loglan Bench.

Compatible with the official Kaggle Benchmarks Python library (kaggle-benchmarks).
Reference: https://github.com/Kaggle/kaggle-benchmarks
"""

import json
from pathlib import Path

# Optional import: kaggle_benchmarks is pre-installed in Kaggle Benchmarks environment
try:
    import kaggle_benchmarks as kbench
    HAS_KBENCH = True
except ImportError:
    HAS_KBENCH = False


def create_kbench_tasks():
    """Register Loglan Benchmark tasks using the official @kbench.task decorator."""
    if not HAS_KBENCH:
        print("kaggle-benchmarks library not installed locally.")
        print("To run in Kaggle: use a Kaggle Benchmarks notebook (https://www.kaggle.com/benchmarks/tasks/new)")
        return

    @kbench.task(name="loglan_syntactic_disambiguation")
    def task_disambiguation(llm, english: str, loglan: str):
        """Evaluate if the model recognizes English ambiguity vs. Loglan single parse tree."""
        prompt = (
            f"Analyze the syntactic structure of the English sentence: \"{english}\"\n"
            f"and compare it with the Loglan translation: \"{loglan}\".\n"
            f"State all valid English parse interpretations, and state whether Loglan has "
            f"multiple parses or exactly one unambiguous parse tree."
        )
        response = llm.prompt(prompt)

        # Built-in kbench assertion: model must assert Loglan has exactly one parse
        kbench.assertions.assert_contains_regex(
            r"(?i)(exactly one|single|unambiguous|one valid)\s+parse",
            response,
            expectation="Model must recognize that Loglan has exactly one valid parse tree."
        )

    @kbench.task(name="loglan_predicate_slot_identification")
    def task_predicate_slots(llm, predicate: str, sentence: str, expected_x1: str, expected_x2: str):
        """Evaluate entity-to-slot mapping for multi-place predicates."""
        prompt = (
            f"Given the Loglan predicate '{predicate}' and the sentence:\n"
            f"\"{sentence}\"\n"
            f"Identify which entity fills slot x1 (agent/donor) and slot x2 (patient/gift)."
        )
        response = llm.prompt(prompt)

        kbench.assertions.assert_contains_regex(
            expected_x1,
            response,
            expectation=f"Slot x1 must contain '{expected_x1}'."
        )
        kbench.assertions.assert_contains_regex(
            expected_x2,
            response,
            expectation=f"Slot x2 must contain '{expected_x2}'."
        )

    print("Successfully registered Loglan tasks with @kbench.task decorator.")


if __name__ == "__main__":
    create_kbench_tasks()
