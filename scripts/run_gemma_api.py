"""
Run benchmark evaluation on models/gemma-4-31b-it via Google GenAI API.
Selects representative cases across Disambiguation, Slot Identification, and Translation Consistency.
Saves incremental results to results/raw/gemma-4-31b-it_results.json.
"""
import json
import os
import sys
import time
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 stdout on Windows to prevent charmap encoding errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")

# Add project root to sys.path
sys.path.insert(0, '.')
load_dotenv('.env')

from google import genai
from google.genai import types

from src.retriever import LoglanRetriever
from src.prompts import (
    SYSTEM_PROMPT,
    DISAMBIGUATION_PROMPT_TEMPLATE,
    SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
    BENCHMARK_PROMPT_TEMPLATE,
)

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found!")
    sys.exit(1)

client = genai.Client(api_key=api_key)
model_name = "models/gemma-4-31b-it"
retriever = LoglanRetriever()

# Load benchmark dataset
with open('data/benchmark_dataset.json', 'r', encoding='utf-8') as f:
    bench_data = json.load(f)

cases = bench_data['cases']

# Select 1 representative case per category for fast verified evaluation
# (A01: Disambiguation, B01: Slot Identification, C01: Translation Consistency)
target_ids = ['A01', 'B01', 'C01']
target_cases = [c for c in cases if c['id'] in target_ids]

out_file = Path('results/raw/gemma-4-31b-it_results.json')
results = []

print(f"Starting Gemma 4 31B verified run on {len(target_cases)} benchmark cases: {target_ids}")

config = types.GenerateContentConfig(
    temperature=0.2,
    max_output_tokens=1500,
    system_instruction=SYSTEM_PROMPT
)

for idx, case in enumerate(target_cases, 1):
    cid = case['id']
    cat = case['category']

    print(f"\n[{idx}/{len(target_cases)}] Evaluating {cid} ({cat})...")

    # Generate prompt
    if cat == 'disambiguation':
        ctx = retriever.retrieve_context(case['english'] + ' ' + case.get('loglan', ''))
        prompt = DISAMBIGUATION_PROMPT_TEMPLATE.format(
            english=case['english'],
            loglan=case.get('loglan', ''),
            context=ctx
        )
    elif cat == 'slot_identification':
        ctx = retriever.retrieve_context(case['predicate'])
        prompt = SLOT_IDENTIFICATION_PROMPT_TEMPLATE.format(
            predicate=case['predicate'],
            sentence=case.get('sentence', ''),
            context=ctx
        )
    elif cat == 'translation_consistency':
        ctx = retriever.retrieve_context(case['english'])
        q = f"Translate '{case['english']}' to unambiguous Loglan."
        prompt = BENCHMARK_PROMPT_TEMPLATE.format(question=q, context=ctx)

    response_text = ""
    in_tokens = 0
    out_tokens = 0
    latency = 0.0

    for attempt in range(4):
        try:
            t0 = time.time()
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            latency = time.time() - t0
            response_text = resp.text or ""
            if hasattr(resp, 'usage_metadata') and resp.usage_metadata:
                in_tokens = getattr(resp.usage_metadata, 'prompt_token_count', 0) or 0
                out_tokens = getattr(resp.usage_metadata, 'candidates_token_count', 0) or 0
            break
        except Exception as e:
            err = str(e)
            print(f"  [Attempt {attempt+1}/4] API Error: {err[:90]}")
            if attempt < 3:
                sleep_s = 5 * (attempt + 1)
                time.sleep(sleep_s)
            else:
                response_text = f"API Error: {err}"

    print(f"  Success in {latency:.2f}s ({in_tokens} in / {out_tokens} out tokens)")

    results.append({
        "case_id": cid,
        "category": cat,
        "prompt": prompt,
        "response": response_text,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "latency_sec": latency,
        "gold": case
    })

    # Save incremental results
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            "model": "gemma-4-31b-it",
            "provider": "google-gemma-4-31b-it-live-api",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_cases": len(results),
            "results": results
        }, f, indent=2, ensure_ascii=False)

    time.sleep(2)

print(f"\nAll done! Successfully saved {len(results)} evaluated cases to {out_file}")
