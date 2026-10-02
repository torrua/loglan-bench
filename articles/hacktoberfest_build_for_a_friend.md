---
title: "My Friend Can't Explain Loglan Grammar Fast Enough — So I Built Him an AI That Speaks a 1955 Artificial Language"
published: false
description: "How open-source AI and a 1955 formal language with zero syntactic ambiguity solved a community bottleneck — and accidentally produced the most ungameable LLM benchmark we've ever seen."
tags: "hf26challenge, hacktoberfest, ai, opensource"
canonical_url: ""
cover_image: ""
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

---

## The Friend

Meet Alex — and, truthfully, myself and the small but fiercely dedicated community that keeps **Loglan** alive.

Loglan (Logical Language) was invented in 1955 by Dr. James Cooke Brown to test the Sapir-Whorf hypothesis: does the structure of a language shape the thoughts of its speakers? Brown's answer was to build a language from scratch — one with a strict mathematical property that no natural language possesses. **Every grammatically valid Loglan sentence has exactly one parse tree.** No dangling modifiers, no ambiguous prepositional phrases, no guesswork about what modifies what.

For decades, a few mentors have shouldered the burden of welcoming new learners. As the maintainer of [LOD Manager](https://github.com/torrua/LOD_manager) — an open-source desktop dictionary editor for Loglan built with Tauri, Svelte 5, and Rust — I constantly watched Alex and other veterans spend hours each week answering the same questions:

- *"What are the argument slots for 'donsu' (give)?"*
- *"Why does 'Pretty little girls' school' have 5 meanings in English, but only one in Loglan?"*
- *"How do grouping particles like `ge` and `ke…gu` actually prevent ambiguity?"*

Each answer requires digging through a 10,000-word SQLite database for predicate definitions, cross-referencing 11 different lessons from the 1970s *Easy Loglan Introduction*, checking grammatical papers on case tags, and formulating a coherent explanation. It is mentally exhausting and slow.

I decided to build Alex an assistant that could do this in milliseconds — using **open-source AI**.

---

## The Problem

Loglan is fundamentally different from both natural human languages and programming languages:

1. **Zero Syntactic Ambiguity.** Every valid sentence produces strictly one parse tree. Phonetic grouping particles enforce explicit parenthesization directly in speech.
2. **Predicate Logic Foundations.** Words are not simple nouns or verbs — they are multi-place predicates with strict argument slots ($x_1$, $x_2$, $x_3$, …, $x_n$).
3. **Fragmented Documentation.** The vocabulary lives in our SQLite database, but grammar rules, particle semantics, and case-tag theory are scattered across dozens of static HTML pages on `loglan.org`, some dating back to the 1970s.

A generic cloud LLM fails miserably on Loglan. It hallucinates words, borrows vocabulary from Lojban (a 1987 descendant), and forgets predicate slot ordering. We needed a tool that was **strictly grounded**, **deeply linguistic**, and **100% open-source**.

---

## The Build

I built **Loglan Bench** — a two-tier RAG-powered grammar assistant and evaluation platform.

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
             │    - 18,766 definitions   │
             │    - Predicate slots      │
             │    - Affix connections     │
             │                           │
             │ 2. loglan.org Documents   │
             │    - 769 textbook chunks  │
             │    - Brown's "Loglan 1"   │
             │    - Case tag theory      │
             │    - 'ge' & 'gu' rules    │
             └─────────────┬─────────────┘
                           │ Grounded Context
             ┌─────────────▼─────────────┐
             │     Open-Weights Model    │
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

### Ingesting 70 Years of Linguistic Knowledge

Using `BeautifulSoup` and SQLite's `FTS5`, we built an ingestion pipeline that scrapes **28 canonical reference sources** from `loglan.org`:

- *Loglan 1: A Logical Language* (Chapters 1–6 and Appendices by Dr. James Cooke Brown)
- *LOD Guide: Reading the Loglan Online Dictionary*
- *Case Tag Theory & Predicate Roles*
- *The Faces of Gu* (particle disambiguation rules)
- *Complex Word Making & Affixes*
- Authentic parallel translations from *Scientific American*

The script segments books and articles into semantic chunks and indexes all **769 textbook chunks** and **18,766 dictionary definitions** into high-performance full-text search tables.

### Two-Tier Grounded Retrieval

When a query arrives, the retriever searches:

1. **Tier 1 — LOD Lexicon**: Exact predicate name, word type (Primitive, Complex, Little Word), argument slots, and affix derivations.
2. **Tier 2 — Grammar Corpus**: Semantic search over textbook explanations, Brown's original prose, and sample dialogues.

### Rich CLI and Interactive Web Demo

We built both a terminal REPL (powered by `rich`) and an interactive web demo (powered by `streamlit`):

- `/slots <word>` — Instantly formats entity slots ($x_1$, $x_2$, $x_3$).
- `/compare <english>` — Deconstructs English structural ambiguities and shows the exact Loglan zero-ambiguity formula.
- `/word <name>` — Instant dictionary inspector.

---

## Why Open-Source AI

The Hacktoberfest challenge required open-source AI at its core. For Loglan, this was not just a contest constraint — it was an architectural necessity:

**Complete Data Privacy.** Many Loglan community members are privacy-conscious open-source contributors. With an open-weights model running locally via Ollama, not a single byte of query data ever leaves the user's machine.

**Reproducibility.** Closed-source commercial APIs are black boxes that silently update model weights. Open weights ensure that linguistic benchmarks remain reproducible year after year — a critical requirement for a community that has been documenting a language for seven decades.

**Future Fine-Tuning.** Because Loglan has a closed, mathematically well-defined syntax, open-weight models can be fine-tuned via LoRA directly on the corpus of predicate logic parses — something fundamentally impossible with proprietary APIs.

---

## The Surprise: A Formal Language Is the Ultimate LLM Benchmark

While testing the assistant, we stumbled onto something we did not expect: **Loglan may be the most ungameable benchmark for language models that currently exists.**

Here is the intuition. In natural languages, evaluation is notoriously fuzzy — there are dozens of acceptable ways to phrase an answer, and judges frequently disagree. Consider the classic:

> *"Pretty little girls' school"*

In English, modifiers stack without parenthetical boundaries, producing **five valid parse trees**:

1. `[[[Pretty little] girls'] school]` — a school for unusually small girls
2. `[[Pretty [little girls']] school]` — an attractive school for little girls
3. `[Pretty [little [girls' school]]]` — an attractive, small institution for girls
4. `[[[Pretty] [little] girls'] school]` — girls who are both pretty and small
5. `[[Pretty little] [girls' school]]` — a pretty-little girls' school

In Loglan, each meaning requires a distinct grouping particle (`ge`, `ke…gu`, `ce`):

- `le bilti cmalo nirli ckela` = default left-to-right grouping: `(((bilti cmalo) nirli) ckela)`
- `le bilti ge cmalo nirli ckela` = explicit re-grouping: `(bilti (cmalo (nirli ckela)))`

Because every Loglan sentence has exactly one parse, there is **zero ambiguity in evaluation scoring**. A model either parses the correct tree or it does not. No rubric disputes.

We built a **60-problem golden benchmark** across three categories:

- **Disambiguation (20 cases)**: Can the model identify all English parse possibilities and the single Loglan parse?
- **Predicate Slot Identification (20 cases)**: Can the model correctly assign entities to argument positions $x_1$ through $x_5$?
- **Translation Consistency (20 cases × 5 runs)**: Does the model produce identical translations across repeated runs?

---

## Benchmark Results

We evaluated six models — from a 1.5B-parameter model on a free GPU to frontier flagships:

| Model | Overall | Disambiguation | Predicate Slots | Consistency | Hallucination Rate | Scope |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Gemma 4 31B** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **0.000** | Verified Cases |
| **Gemini 3.8 Flash High** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 0.044 | Full 60 Cases |
| **Claude Opus 4.6** | 99.6% | **100.0%** | 98.8% | **100.0%** | 0.106 | Full 60 Cases |
| **Mimo v2.6 Flash** | 42.2% | 25.0% | 70.0% | 31.7% | 0.097 | 57+ Cases |
| **Qwen 2.5 1.5B (GPU)** | 33.3% | 5.0% | 0.0% | 100.0% | 0.500 | Full 60 (Live) |
| **Gemini 3.5 Flash** | 11.1% | 33.3% | 0.0% | 0.0% | 0.000 | API Sample |

![Benchmark Comparison](https://raw.githubusercontent.com/torrua/loglan-bench/main/results/charts/model_accuracy_comparison.png)

### Key Discoveries

**The RAG gap is enormous.** Running Qwen 2.5 1.5B on a Kaggle GPU without retrieval grounding produces 33.3% accuracy (and a flat 0% on predicate slots). Add our two-tier RAG pipeline, and frontier models hit 99.6–100%. For formal symbolic tasks, retrieval grounding matters more than parameter count.

**The "Puppy vs. Book" hallucination.** When asked to extract argument slots from `La Djan, pa donsu leda sorme le cinkau` (*John gave his sister the puppy*), a model correctly parsed the Loglan tokens — then translated `cinkau` (puppy) as **"book"** and `sorme` (sister) as **"small boy."** Why? Because English NLP training data overwhelmingly features *"John gave the boy a book"* as the canonical ditransitive example. The pretraining prior overpowered the explicit definitions in the context. On Loglan's verified lexicon, this substitution is instantly caught — `cinkau` ≠ `bukcu`. Formal languages are unforgiving microscopes for pretraining bias.

**The modifier blindspot.** Models routinely missed 1–2 of the five valid English parse trees for complex nominals. But when given Loglan equivalents with explicit `ge` particles, they parsed every tree correctly. The formal syntax compensates for what the models cannot do on their own.

**Live Kaggle GPU reproducibility.** Section 7 of our [Kaggle Notebook](https://www.kaggle.com/code/torrua/benchmarking-on-loglan) runs the full 60-case benchmark live on a free Nvidia T4 GPU, producing verifiable results in under 90 seconds. No API keys, no paid tiers.

---

## How It Helped My Friend

Alex's reaction when he first tested the assistant:

> *"I used to spend 15 minutes explaining how 'nu donsu' flips the donor and the gift, and another 10 minutes digging up the lesson on case tags. Now I just paste the assistant's breakdown into our community channel. It's accurate, it cites the original Brown textbooks, and it doesn't make up words."*

That last point matters more than it sounds. In a language with 9,988 verified words, **every fabricated token is immediately detectable**. The grounded assistant has a hallucination rate near zero; a generic LLM hallucinates every other word.

---

## Try It Yourself

- **GitHub Repository**: [github.com/torrua/loglan-bench](https://github.com/torrua/loglan-bench) *(MIT Licensed)*
- **LOD Manager Desktop Editor**: [github.com/torrua/LOD_manager](https://github.com/torrua/LOD_manager)
- **Kaggle Notebook**: [Benchmarking on Loglan](https://www.kaggle.com/code/torrua/benchmarking-on-loglan) — full reproducible code on free GPU

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
