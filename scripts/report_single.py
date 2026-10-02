"""Compute Loglan Bench metrics for one raw results file (no chart overwrites).

Usage:
    python scripts/report_single.py results/raw/<model>_results.json [--per-case]
                                                     [--real-only] [--min-len 400]

--real-only filters out "non-answers": empty completions and short tool-narration
preamble ("I'll ground this... Let me pull...") below --min-len characters.
The length distribution of this runner is bimodal (<400 or >=2000), so the cut is clean.
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.evaluate import (  # noqa: E402
    load_lod_valid_words,
    score_disambiguation,
    score_slots,
    score_consistency,
    score_hallucinations,
)

CATS = ("disambiguation", "slot_identification", "translation_consistency")


def is_real(text: str, min_len: int) -> bool:
    return bool(text) and len(text) >= min_len


def real_item(item: dict, min_len: int) -> dict | None:
    """Return a copy of the item containing only real-answer runs, or None."""
    if item["category"] == "translation_consistency":
        runs = [r for r in item.get("repeated_runs", []) if is_real(r.get("response", ""), min_len)]
        if len(runs) < 2:
            return None
        copy = dict(item)
        copy["repeated_runs"] = runs
        copy["response"] = runs[0]["response"]
        return copy
    return item if is_real(item.get("response", ""), min_len) else None


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def score_all(results, valid_words, min_len, real_only, per_case):
    buckets = {c: [] for c in CATS}
    halluc, latencies = [], []
    used = {c: 0 for c in CATS}

    for item in results:
        it = real_item(item, min_len) if real_only else item
        if real_only and it is None:
            continue
        used[item["category"]] += 1
        latencies.append(item.get("latency_sec", 0.0))
        halluc.append(score_hallucinations(it, valid_words))

        if item["category"] == "disambiguation":
            acc, _ = score_disambiguation(it)
            buckets["disambiguation"].append(acc)
        elif item["category"] == "slot_identification":
            buckets["slot_identification"].append(score_slots(it))
        else:
            buckets["translation_consistency"].append(score_consistency(it))

        if per_case:
            print(f"  {item['case_id']:4s} {item['category']:24s} {buckets[item['category']][-1]:.2f}")

    dis = mean(buckets["disambiguation"])
    slot = mean(buckets["slot_identification"])
    cons = mean(buckets["translation_consistency"])
    return {
        "overall": (dis + slot + cons) / 3,
        "dis": dis,
        "slot": slot,
        "cons": cons,
        "halluc": mean(halluc),
        "lat": mean(latencies),
        "n": {c: (len(buckets[c]), used[c]) for c in CATS},
        "n_cases": sum(used.values()),
        "latencies": latencies,
    }


def print_table(title, m):
    rows = [
        ("Cases with score", f"{m['n_cases']}"),
        ("Overall accuracy", f"{m['overall']:.1%}"),
        ("Disambiguation", f"{m['dis']:.1%}   ({m['n']['disambiguation'][0]}/{m['n']['disambiguation'][1]} cases)"),
        ("Predicate slots", f"{m['slot']:.1%}   ({m['n']['slot_identification'][0]}/{m['n']['slot_identification'][1]} cases)"),
        ("Translation consistency", f"{m['cons']:.1%}   ({m['n']['translation_consistency'][0]}/{m['n']['translation_consistency'][1]} cases)"),
        ("Hallucination rate (vs LOD)", f"{m['halluc']:.1%}"),
        ("Avg latency per case (s)", f"{m['lat']:.1f}"),
    ]
    width = max(len(k) for k, _ in rows)
    print(f"\n=== {title} ===")
    for k, v in rows:
        print(f"{k:<{width}} | {v}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = Path(sys.argv[1])
    per_case = "--per-case" in sys.argv
    real_only = "--real-only" in sys.argv
    min_len = 400
    if "--min-len" in sys.argv:
        min_len = int(sys.argv[sys.argv.index("--min-len") + 1])

    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results", [])
    valid_words = load_lod_valid_words()

    # --- completion quality breakdown (all completions) ---
    print("\n=== Completion quality (all completions) ===")
    print(f"{'category':<24} {'total':>5} {'real':>5} {'short':>6} {'empty':>6}  real-len(med/min/max)")
    all_texts = []
    for c in CATS:
        items = [r for r in results if r["category"] == c]
        texts = (
            [r.get("response", "") for r in items]
            if c != "translation_consistency"
            else [x.get("response", "") for r in items for x in r.get("repeated_runs", [])]
        )
        real = [t for t in texts if is_real(t, min_len)]
        short = [t for t in texts if t and len(t) < min_len]
        empty = [t for t in texts if not t]
        all_texts += texts
        if real:
            lens = [len(t) for t in real]
            stat = f"{statistics.median(lens):.0f} / {min(lens)} / {max(lens)}"
        else:
            stat = "-"
        print(f"{c:<24} {len(texts):>5} {len(real):>5} {len(short):>6} {len(empty):>6}  {stat}")
    n_real = sum(1 for t in all_texts if is_real(t, min_len))
    n_short = sum(1 for t in all_texts if t and len(t) < min_len)
    n_empty = sum(1 for t in all_texts if not t)
    print(f"{'TOTAL':<24} {len(all_texts):>5} {n_real:>5} {n_short:>6} {n_empty:>6}"
          f"   real={n_real/len(all_texts):.1%}")

    print_table("Metrics: ALL completions (as-is)", score_all(results, valid_words, min_len, False, per_case))
    print_table(f"Metrics: REAL answers only (len >= {min_len})",
                score_all(results, valid_words, min_len, True, per_case))

    if real_only:
        m = score_all(results, valid_words, min_len, True, False)
        if m["latencies"]:
            print(f"\nlatency of real-answer cases: med={statistics.median(m['latencies']):.1f}s "
                  f"min={min(m['latencies']):.1f}s max={max(m['latencies']):.1f}s")


if __name__ == "__main__":
    main()
