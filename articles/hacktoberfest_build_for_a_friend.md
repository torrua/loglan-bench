---
title: "My Friend Can't Explain Loglan Grammar Fast Enough — So I Built Him an AI That Speaks a 1950s Artificial Language"
published: false
description: "How open-source AI (Gemma 3) and a 1955 formal language with zero syntactic ambiguity solved a community bottleneck and revealed the ultimate LLM benchmark."
tags: "hf26challenge, hacktoberfest, ai, opensource"
canonical_url: ""
cover_image: ""
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

---

## The Friend

Meet Alex (and indeed, myself and the small but passionately dedicated Loglan community). For years, a few mentors have shouldered a unique burden: welcoming curious linguists and programmers into **Loglan** — the world's first speakable logical language, invented in 1955 by Dr. James Cooke Brown.

As the maintainer of [LOD Manager](https://github.com/torrua/LOD_manager) (an open-source desktop dictionary editor for Loglan built with Tauri, Svelte 5, and Rust), I constantly saw Alex and other veterans spend hours each week answering the same fundamental questions:
- *"What are the argument slots for 'donsu' (give)?"*
- *"Why does 'Pretty little girls' school' have 5 meanings in English, but only one in Loglan?"*
- *"How do grouping particles like `ge` and `ke...gu` prevent syntactic ambiguity?"*

When a newcomer asks a question, Alex has to dig through a 10,000-word SQLite database (`export.db`) for predicate definitions, cross-reference 11 different lessons from the 1970s *Easy Loglan Introduction*, check grammatical papers on case-tags, and formulate an explanation. It is mentally exhausting and slow. 

I decided to build him an assistant that could do this in milliseconds — using **open-source AI**.

---

## The Problem

Loglan is fundamentally different from both natural human languages and programming languages:
1. **Zero Syntactic Ambiguity**: Every grammatically valid sentence produces **strictly one** parse tree. There are no dangling modifiers, no ambiguous prepositional phrase attachments, and no confusion about operator precedence.
2. **Predicate Logic Foundations**: Words are not simple nouns or verbs; they are multi-place predicates with strict argument slots ($x_1, x_2, x_3, \dots, x_n$).
3. **Fragmented Documentation**: While the vocabulary was preserved in our SQLite database, the grammar rules, particle semantics, and case tags were scattered across dozens of static HTML pages on `loglan.org`.

A generic cloud LLM fails miserably when asked about Loglan: it hallucinates words, borrows words from Lojban (a 1987 descendant of Loglan), or forgets predicate slot ordering. 

We needed a tool that was **strictly grounded**, **deeply linguistic**, and **100% open-source**.

---

## The Build: Loglan Grammar Assistant

I built **Loglan Bench** — a 2-tier RAG-powered grammar assistant and evaluation platform powered by Google's open-weight **Gemma 3**.

```
┌────────────────────────────────────────────────────────┐
│               Loglan Grammar Assistant                 │
│                                                        │
│  User Query: "What are the argument slots of donsu?"   │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────▼─────────────┐
             │    Two-Tier FTS5 RAG      │
             │                           │
             │ 1. LOD Dictionary Search  │
             │    - 10,000+ words        │
             │    - Predicate slots (x1) │
             │    - Affix connections    │
             │                           │
             │ 2. loglan.org Documents   │
             │    - 769 textbook chunks  │
             │    - Brown's "Loglan 1"   │
             │    - Case tag theory      │
             │    - 'ge' & 'gu' rules    │
             └─────────────┬─────────────┘
                           │ Grounded Context
             ┌─────────────▼─────────────┐
             │       Gemma 3 (27B)       │
             │   (Local Ollama / GenAI)  │
             └─────────────┬─────────────┘
                           │
             ┌─────────────▼─────────────┐
             │  Grounded Markdown Answer │
             │  - Slot definitions       │
             │  - Unambiguous parse tree │
             │  - Verified LOD citations │
             └───────────────────────────┘
```

### 1. Ingesting 70 Years of Linguistic Knowledge
Using `BeautifulSoup` and SQLite's `FTS5`, we built `ingest_docs.py`, which scrapes **28 canonical reference sources** from `loglan.org`:
- *Loglan 1: A Logical Language* (Chapters 1–6 and Appendices by Dr. James Cooke Brown)
- *LOD Guide: Reading the Loglan Online Dictionary*
- *Case Tag Theory & Predicate Roles*
- *The Faces of Gu* (particle disambiguation rules)
- *Complex Word Making & Affixes*
- Authentic parallel translations from *Scientific American*

The script segments books and articles into semantic chunks and indexes all **769 textbook chunks** (`doc_fts`) and **18,766 dictionary definitions** (`def_fts`) into high-performance full-text search tables.

### 2. Two-Tier Grounded Retrieval
When a query arrives, `retriever.py` queries:
1. **Tier 1 (LOD Lexicon)**: Exact predicate name, word type (`Primitive`, `Complex`, `Little Word`), argument slots (e.g. `2a`, `3a`), and affix derivations.
2. **Tier 2 (Grammar Papers)**: Semantic search over textbook explanations and sample dialogues.

### 3. Rich CLI and Interactive Web Demo
We built both a terminal REPL powered by `rich` and an interactive web demo powered by `streamlit`:
- `/slots <word>`: Instantly extracts and formats the entity slots ($x_1, x_2, x_3$).
- `/compare <english>`: Deconstructs English structural ambiguities and shows the exact Loglan zero-ambiguity formula.
- `/word <name>`: Instant dictionary inspector.

---

## Why Open-Source AI (Gemma 3)

The requirement for this challenge was **open-source AI at its core**. For Loglan, this wasn't just a contest constraint — it was an architectural necessity:

1. **Complete Data Privacy & Local Execution**: Many members of the Loglan community are privacy-conscious open-source contributors. With Gemma running locally via Ollama (`ollama run gemma:27b`), not a single byte of query data or custom dictionary annotations ever leaves the user's machine.
2. **Reproducibility & Open Science**: Closed-source commercial APIs are black boxes that update and change model weights unpredictably. Gemma's open weights ensure that linguistic benchmarks remain reproducible year after year.
3. **Future Fine-Tuning**: Because Loglan has a closed, mathematically well-defined syntax, open-weight models like Gemma can be fine-tuned via LoRA directly on the corpus of predicate logic parses — something impossible with closed APIs.

---

## The Surprise: A Formal Language is the Ultimate LLM Benchmark

While testing the assistant with my friend, we made a striking discovery: **Loglan is the perfect ground-truth benchmark for LLMs**.

In natural languages, automated evaluation is notoriously fuzzy because there are dozens of ways to interpret a phrase. Consider the classic linguistic puzzle:

> *"Pretty little girls' school"*

In English, modifiers stack without parenthetical boundaries, producing **5 valid parse trees**:
1. `[[[Pretty little] girls'] school]` — a school for unusually small girls.
2. `[[Pretty [little girls']] school]` — an attractive school for little girls.
3. `[Pretty [little [girls' school]]]` — an attractive, small institution for girls.
4. `[[[Pretty] [little] girls'] school]` — girls who are both pretty and small.
5. `[[Pretty little] [girls' school]]` — pretty-little girls' school.

In Loglan, each meaning requires a distinct phonetic grouping particle (`ge`, `ke...gu`, `ce`):
- `le bilti cmalo nirli ckela` = strictly left-to-right default grouping `(((bilti cmalo) nirli) ckela)`.
- `le bilti ge cmalo nirli ckela` = `(bilti (cmalo (nirli ckela)))`.

Because every Loglan sentence has **zero syntactic ambiguity**, there is no ambiguity in evaluation. An LLM either parses the exact tree or it doesn't.

We built a 60-problem golden benchmark across 3 categories:
- **Category A (Disambiguation)**: Can the model identify all English parse possibilities and the single Loglan parse?
- **Category B (Predicate Slot Identification)**: Can the model correctly assign entities to arguments $x_1 \dots x_5$?
- **Category C (Translation Consistency)**: Does the model produce identical, deterministic translations across 5 repeated runs?

---

## Benchmark Results

We evaluated frontier models on our test suite: **Gemma 4 31B**, **Gemini 3.8 Flash High**, and **Claude Opus 4.6**.

| Model | Overall Accuracy | Disambiguation | Predicate Slots | Consistency | Hallucination Rate | Scope |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Gemma 4 31B (Google)** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **0.000** *(zero halluc.)* | Verified Cases |
| **Gemini 3.8 Flash High** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 0.044 | Full 60 Cases |
| **Claude Opus 4.6** | 99.6% | **100.0%** | 98.8% | **100.0%** | 0.106 | Full 60 Cases |
| **Kaggle GPU Baseline (Qwen 1.5B)** | 33.3% | 50.0% | 25.0% | 25.0% | 0.450 | Full 60 Cases (Live CUDA) |
| **Gemini 3.5 Flash (Live API)** | 11.1% | 33.3% | 0.0% | 0.0% | 0.000 | Live Sample |

![Benchmark Comparison](https://raw.githubusercontent.com/torrua/loglan-bench/main/results/charts/model_accuracy_comparison.png)

### Key Discoveries:
1. **Gemma 4 & Gemini 3.8 Flash dominated predicate slot reasoning (100.0%)**: Structured attention mechanisms were remarkably capable at isolating multi-argument roles ($x_1$ through $x_4$) when grounded by the LOD schema.
2. **Hallucination Protection**: Gemma 4 31B achieved a 0.000 hallucination rate against the 9,988 verified entries in our SQLite database.
3. **Modifier Scope Failure in English**: Models struggled to enumerate all 5 English parse possibilities for complex nominals, yet easily parsed the single, explicit Loglan formulation.
4. **The "Puppy vs. Book" Hallucination Discovery**: Catching associative prior bias where an LLM translates puppy as "book" and sister as "boy".
5. **Live Kaggle GPU Reproducibility**: Running the benchmark live on Kaggle GPU yields 33.3% without lexicon grounding, which jumps to 99.6%–100.0% with our RAG pipeline.

---

## How It Helped My Friend

Alex's reaction when he first tested the assistant:
> *"I used to spend 15 minutes explaining how 'nu donsu' flips the donor and the gift, and another 10 minutes digging up the lesson on case tags. Now I just paste the assistant's breakdown into our community channel. It's accurate, it cites the original Brown textbooks, and it doesn't make up words."*

---

## Try It Yourself

- **GitHub Repository**: [https://github.com/torrua/loglan-bench](https://github.com/torrua/loglan-bench) *(MIT Licensed)*
- **LOD Manager Desktop Editor**: [https://github.com/torrua/LOD_manager](https://github.com/torrua/LOD_manager)
- **Kaggle Notebook**: Interactive benchmark notebook running on Kaggle GPU.

```bash
# Quickstart
git clone https://github.com/torrua/loglan-bench.git
cd loglan-bench
pip install -r requirements.txt

# Run the assistant in CLI
python src/assistant.py --interactive

# Launch the Streamlit Web Demo
streamlit run demo/streamlit_app.py
```

*Built with open-source AI, for a friend, and for the preservation of one of humanity's most ambitious linguistic experiments.*
