"""
Run full benchmark on Gemini 3.5 Flash via official Google GenAI Live API.
Includes robust retry logic, polite rate limiting, and incremental progress saving.
"""
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

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
    print("ERROR: GOOGLE_API_KEY / GEMINI_API_KEY not found in environment!")
    sys.exit(1)

client = genai.Client(api_key=api_key)
model_name = "gemini-3.5-flash"
retriever = LoglanRetriever()

# Load all 60 cases
with open('data/benchmark_dataset.json', 'r', encoding='utf-8') as f:
    bench_data = json.load(f)

cases = bench_data['cases']
out_file = Path('results/raw/gemini-3.5-flash_results.json')

# Load existing progress if available
existing_results = []
done_ids = set()
if out_file.exists():
    try:
        with open(out_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing_results = data.get('results', [])
            done_ids = {r['case_id'] for r in existing_results}
            print(f"Resuming: found {len(done_ids)} existing results in {out_file}")
    except Exception:
        pass

print(f"Starting Gemini 3.5 Flash Live API benchmark on {len(cases)} cases (already done: {len(done_ids)})")

config = types.GenerateContentConfig(
    temperature=0.2,
    max_output_tokens=1500,
    system_instruction=SYSTEM_PROMPT
)

for idx, case in enumerate(cases, 1):
    cid = case['id']
    cat = case['category']
    if cid in done_ids:
        continue

    print(f"\n[{idx}/{len(cases)}] Processing {cid} ({cat})...")

    # Build prompt
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

    # Execute with retry loop
    response_text = ""
    in_tokens = 0
    out_tokens = 0
    latency = 0.0

    for attempt in range(5):
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
            print(f"  ✓ Success in {latency:.2f}s ({in_tokens} in / {out_tokens} out tokens)")
            break
        except Exception as e:
            err_str = str(e)
            print(f"  [Attempt {attempt+1}/5] Error: {err_str[:90]}")
            if attempt < 4:
                sleep_time = 3 * (attempt + 1)
                print(f"  Sleeping {sleep_time}s before retry...")
                time.sleep(sleep_time)
            else:
                response_text = f"API Error after 5 attempts: {err_str}"

    existing_results.append({
        "case_id": cid,
        "category": cat,
        "prompt": prompt,
        "response": response_text,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "latency_sec": latency,
        "gold": case
    })
    done_ids.add(cid)

    # Save incremental progress
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            "model": model_name,
            "provider": "google-genai-live-api",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_cases": len(existing_results),
            "results": existing_results
        }, f, indent=2, ensure_ascii=False)

    # Polite rate limit sleep
    time.sleep(1.2)

print(f"\nCompleted Gemini 3.5 Flash Live API run: {len(existing_results)} cases saved to {out_file}")
