"""Generate all 60 benchmark prompts with RAG context for full Claude evaluation."""
import json
import sys
sys.path.insert(0, '.')

from src.retriever import LoglanRetriever
from src.prompts import (
    SYSTEM_PROMPT,
    DISAMBIGUATION_PROMPT_TEMPLATE,
    SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
    BENCHMARK_PROMPT_TEMPLATE,
)

retriever = LoglanRetriever()

with open('data/benchmark_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

cases = data['cases']
prompts = []

for case in cases:
    cid = case['id']
    cat = case['category']

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

    prompts.append({
        'case_id': cid,
        'category': cat,
        'prompt': prompt,
        'gold': case
    })

# Save all prompts
with open('scripts/all_prompts.json', 'w', encoding='utf-8') as f:
    json.dump(prompts, f, indent=2, ensure_ascii=False)

# Also save system prompt for reference
with open('scripts/system_prompt.txt', 'w', encoding='utf-8') as f:
    f.write(SYSTEM_PROMPT)

# Split into 4 batches for parallel subagent processing
batch_size = 15
for i in range(4):
    batch = prompts[i*batch_size:(i+1)*batch_size]
    with open(f'scripts/batch_{i+1}.json', 'w', encoding='utf-8') as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)
    cats = {}
    for p in batch:
        cats[p['category']] = cats.get(p['category'], 0) + 1
    print(f"Batch {i+1}: {len(batch)} cases - {cats}")

print(f"\nTotal: {len(prompts)} prompts generated and split into 4 batches")
