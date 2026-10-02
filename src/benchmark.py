"""Benchmark runner for Loglan Bench: evaluates LLMs across zero-ambiguity tasks."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x, **kwargs):
        return x

try:
    from src.config import DATA_DIR, RAW_RESULTS_DIR
    from src.retriever import LoglanRetriever
    from src.prompts import (
        SYSTEM_PROMPT,
        DISAMBIGUATION_PROMPT_TEMPLATE,
        SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
        BENCHMARK_PROMPT_TEMPLATE,
    )
    from src.models import get_model_provider
except ImportError:
    from config import DATA_DIR, RAW_RESULTS_DIR
    from retriever import LoglanRetriever
    from prompts import (
        SYSTEM_PROMPT,
        DISAMBIGUATION_PROMPT_TEMPLATE,
        SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
        BENCHMARK_PROMPT_TEMPLATE,
    )
    from models import get_model_provider


def load_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cases", [])


def run_benchmark(
    models: List[str],
    dataset_path: Path = DATA_DIR / "benchmark_dataset.json",
    output_dir: Path = RAW_RESULTS_DIR,
    limit: int = 0,
    category_filter: str = "",
    consistency_runs: int = 5,
    mock: bool = False,
):
    """Run benchmark evaluation across specified models."""
    cases = load_dataset(dataset_path)
    if category_filter:
        cases = [c for c in cases if c.get("category") == category_filter]
    if limit > 0:
        cases = cases[:limit]

    print(f"\nLoaded {len(cases)} test cases from {dataset_path}")
    print(f"Models to evaluate: {models}")
    print(f"Output directory: {output_dir}\n")

    retriever = LoglanRetriever()

    for model_name in models:
        clean_model_tag = model_name.replace("/", "_").replace(":", "_")
        out_file = output_dir / f"{clean_model_tag}_results.json"
        print(f"=== Running evaluation for model: {model_name} ===")

        provider = get_model_provider(
            model_name=model_name,
            mock=mock or model_name.startswith("mock")
        )

        model_results = []
        for case in tqdm(cases, desc=f"Evaluating {model_name}"):
            cid = case["id"]
            cat = case["category"]

            # 1. Category A: Disambiguation
            if cat == "disambiguation":
                ctx = retriever.retrieve_context(case["english"] + " " + case.get("loglan", ""))
                prompt = DISAMBIGUATION_PROMPT_TEMPLATE.format(
                    english=case["english"],
                    loglan=case.get("loglan", ""),
                    context=ctx
                )
                resp = provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
                model_results.append({
                    "case_id": cid,
                    "category": cat,
                    "prompt": prompt,
                    "response": resp.content,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                    "latency_sec": resp.latency_sec,
                    "gold": case
                })

            # 2. Category B: Slot Identification
            elif cat == "slot_identification":
                ctx = retriever.retrieve_context(case["predicate"])
                prompt = SLOT_IDENTIFICATION_PROMPT_TEMPLATE.format(
                    predicate=case["predicate"],
                    sentence=case.get("sentence", ""),
                    context=ctx
                )
                resp = provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
                model_results.append({
                    "case_id": cid,
                    "category": cat,
                    "prompt": prompt,
                    "response": resp.content,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                    "latency_sec": resp.latency_sec,
                    "gold": case
                })

            # 3. Category C: Translation Consistency (multiple runs)
            elif cat == "translation_consistency":
                ctx = retriever.retrieve_context(case["english"])
                q = f"Translate '{case['english']}' to unambiguous Loglan."
                prompt = BENCHMARK_PROMPT_TEMPLATE.format(question=q, context=ctx)

                runs_output = []
                for run_idx in range(consistency_runs):
                    resp = provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3)
                    runs_output.append({
                        "run_index": run_idx + 1,
                        "response": resp.content,
                        "latency_sec": resp.latency_sec
                    })

                model_results.append({
                    "case_id": cid,
                    "category": cat,
                    "prompt": prompt,
                    "response": runs_output[0]["response"],
                    "repeated_runs": runs_output,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                    "gold": case
                })

        output_dir.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({
                "model": model_name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_cases": len(model_results),
                "results": model_results
            }, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {out_file}\n")


def main():
    parser = argparse.ArgumentParser(description="Loglan Bench Evaluation Runner")
    parser.add_argument("--models", type=str, default="mock-gemma", help="Comma-separated list of models")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of test cases")
    parser.add_argument("--category", type=str, default="", help="Filter by category")
    parser.add_argument("--runs", type=int, default=3, help="Number of consistency runs for Category C")
    parser.add_argument("--mock", action="store_true", help="Force mock provider")
    args = parser.parse_args()

    model_list = [m.strip() for m in args.models.split(",") if m.strip()]
    run_benchmark(
        models=model_list,
        limit=args.limit,
        category_filter=args.category,
        consistency_runs=args.runs,
        mock=args.mock
    )


if __name__ == "__main__":
    main()
