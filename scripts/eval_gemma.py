import json
import sys
sys.path.insert(0, '.')

from src.evaluate import (
    score_disambiguation,
    score_slots,
    score_hallucinations,
    load_lod_valid_words,
)

with open('results/raw/gemma-4-31b-it_results.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

valid_words = load_lod_valid_words()

print(f"Model: {d['model']}")
print(f"Provider: {d['provider']}")
print(f"Timestamp: {d['timestamp']}\n")

total_disambig = 0
total_slot = 0
total_consist = 0
total_halluc = 0

for r in d['results']:
    cid = r['case_id']
    cat = r['category']
    print(f"=== CASE {cid} ({cat}) ===")
    print(f"Latency: {r['latency_sec']:.2f}s | Tokens: {r['input_tokens']} in, {r['output_tokens']} out")
    print(f"Response Preview:\n{r['response'][:300]}...\n")
    
    halluc = score_hallucinations(r, valid_words)
    total_halluc += halluc
    
    if cat == 'disambiguation':
        acc, cnt = score_disambiguation(r)
        total_disambig += acc
        print(f"-> Disambiguation Accuracy: {acc:.2f} (count match: {cnt:.2f}, halluc: {halluc:.3f})\n")
    elif cat == 'slot_identification':
        acc = score_slots(r)
        total_slot += acc
        print(f"-> Slot Identification Accuracy: {acc:.2f} (halluc: {halluc:.3f})\n")
    elif cat == 'translation_consistency':
        gold = r.get('gold', {})
        parts = gold.get('key_particles', [])
        match = sum(1 for p in parts if p.lower() in r['response'].lower()) / len(parts) if parts else 1.0
        total_consist += match
        print(f"-> Particle Consistency: {match:.2f} (halluc: {halluc:.3f})\n")

overall = (total_disambig + total_slot + total_consist) / 3
avg_halluc = total_halluc / 3
avg_lat = sum(r['latency_sec'] for r in d['results']) / 3

print("="*60)
print("GEMMA 4 31B EVALUATION SUMMARY:")
print(f"Overall Accuracy:            {overall:.3f}")
print(f"Disambiguation Accuracy:     {total_disambig:.3f}")
print(f"Slot Identification Accuracy:{total_slot:.3f}")
print(f"Translation Consistency:     {total_consist:.3f}")
print(f"Average Hallucination Rate:  {avg_halluc:.3f}")
print(f"Average Latency:             {avg_lat:.2f}s")
print("="*60)
