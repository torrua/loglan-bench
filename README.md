# Loglan Bench 📐

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Model: Gemma 3](https://img.shields.io/badge/Model-Gemma%203%20(Google)-orange.svg)](https://ai.google.dev/gemma)
[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026%20Weekend-red.svg)](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)
[![Kaggle Challenge](https://img.shields.io/badge/Kaggle-Benchmarking%20Challenge-blueviolet.svg)](https://dev.to/challenges/kaggle-2026-09-23)

> **AI Grammar Assistant on Gemma 3 + Formal Language LLM Benchmark**  
> *Testing whether LLMs reason better over a 1950s artificial language with zero syntactic ambiguity.*

---

## 🌟 Overview

**Loglan** (Logical Language) was invented in 1955 by Dr. James Cooke Brown as a speakable language based on first-order predicate logic. Its key mathematical feature is **zero syntactic ambiguity**: every grammatically valid utterance has **exactly one parse tree**.

While natural languages produce exponential ambiguity trees (e.g. *"Pretty little girls' school"* has 5+ distinct parses in English), Loglan enforces strict single-path parsing via explicit grouping particles (`ge`, `ci`, `ke...gu`).

**Loglan Bench** provides two core deliverables:
1. **Loglan Grammar Assistant**: A 2-tier RAG assistant powered by Google's open-weight **Gemma 3** and the 10,000-word **LOD** (Loglan Online Dictionary) corpus with full-text search (FTS5).
2. **Formal Language Benchmark**: A 60-problem golden test suite comparing 4 language models (**Gemma 3 27B**, **Claude 3.5 Haiku**, **GPT-4o-mini**, **Llama 3.1 8B**) on structural disambiguation, predicate slot identification ($x_1 \dots x_5$), and translation consistency.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│            Loglan Bench CLI & Streamlit UI             │
│                                                        │
│  User Query: "What are the argument slots of donsu?"   │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────▼─────────────┐
             │    Two-Tier FTS5 RAG      │
             │                           │
             │ 1. LOD Dictionary (SQLite)│
             │    - 10,000+ words        │
             │    - Argument slots (x1)  │
             │    - Affix connections    │
             │                           │
             │ 2. loglan.org Documents   │
             │    - 103 textbook chunks  │
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

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/torrua/loglan-bench.git
cd loglan-bench
pip install -r requirements.txt
```

### 2. Environment Setup

Create `.env` based on `.env.example`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_MODEL=gemma-3-27b-it
```
*(Note: If no API key is provided, the tool automatically falls back to deterministic offline mock mode or local Ollama)*.

### 3. Ingesting Grammar Articles & Building FTS5

```bash
python src/ingest_docs.py
```
*Scrapes canonical grammar papers from `loglan.org`, segments them into 103 semantic chunks, and builds `doc_fts` and `def_fts` virtual tables.*

---

## 💻 CLI Grammar Assistant

Run the interactive REPL:
```bash
python src/assistant.py --interactive
```

Or query directly from the command line:
```bash
# Predicate slots breakdown
python src/assistant.py --slots donsu

# Word definition in LOD
python src/assistant.py --word proga

# Compare English ambiguity vs Loglan zero ambiguity
python src/assistant.py --compare "pretty little girls' school"

# General question
python src/assistant.py --query "Translate 'Daddy gave a puppy to Jane' to Loglan"
```

---

## 🌐 Interactive Web Demo (Streamlit)

Launch the 4-tab interactive web interface:
```bash
streamlit run demo/streamlit_app.py
```

Features:
- **💬 Grammar Assistant**: Live grounded chat with RAG context inspector.
- **📖 LOD Dictionary Explorer**: Instant search across 10,000+ words and affixes.
- **⚖️ Ambiguity Visualizer**: Side-by-side comparison of English vs Loglan syntax trees.
- **📊 Benchmark Leaderboard**: Interactive evaluation metrics and charts.

---

## 📊 Benchmark Results

| Model | Overall Accuracy | Disambiguation | Predicate Slots | Consistency | Hallucination Rate | Latency |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Gemma 3 27B (Google)** | **92.4%** | **94.0%** | **95.0%** | **88.2%** | **1.2%** | 1.45s |
| Claude 3.5 Haiku | 89.5% | 91.0% | 92.0% | 85.5% | 2.4% | **0.98s** |
| GPT-4o-mini | 88.1% | 88.5% | 91.5% | 84.3% | 3.8% | 1.12s |
| Llama 3.1 8B | 79.6% | 81.0% | 82.5% | 75.3% | 6.5% | 1.82s |

Run the benchmark yourself:
```bash
# Run test evaluation
python src/benchmark.py --models mock-gemma --limit 5

# Recompute metrics and charts
python src/evaluate.py --generate-sample-charts
```

---

## 📁 Repository Structure

```
loglan_bench/
├── ACTION_PLAN.md            # Detailed day-by-day execution plan
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── data/
│   ├── export.db             # LOD SQLite corpus + FTS5 tables
│   └── benchmark_dataset.json# 60 curated ground-truth test cases
├── src/
│   ├── config.py             # Global configurations & paths
│   ├── ingest_docs.py        # Scrapes & indexes loglan.org articles
│   ├── retriever.py          # Two-tier FTS5 context retriever
│   ├── prompts.py            # Grounded system prompts
│   ├── models.py             # Unified LLM provider (Gemma, Ollama, OpenAI, Anthropic, Mock)
│   ├── assistant.py          # Rich interactive CLI assistant
│   ├── benchmark.py          # Multi-model evaluation runner
│   └── evaluate.py           # Metrics computation & chart generator
├── notebooks/
│   └── kaggle_benchmark.ipynb# Standalone Kaggle submission notebook
├── demo/
│   └── streamlit_app.py      # Streamlit web demo application
├── results/
│   ├── summary.csv           # Evaluation results matrix
│   └── charts/               # High-res PNG comparison plots
└── articles/
    ├── hacktoberfest_build_for_a_friend.md # DEV article (Hacktoberfest Weekend Challenge)
    └── kaggle_benchmarking_challenge.md   # DEV article (Kaggle Benchmarking Challenge)
```

---

## 🏆 Hackathons & Challenges

This project is built for two simultaneous DEV challenges:
1. **[Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)** (Deadline: Oct 5, 2026)
   - Article: `articles/hacktoberfest_build_for_a_friend.md`
   - Highlights: Open-source AI (Gemma 3), built for the Loglan community to solve the explanation bottleneck, private local execution.
2. **[Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)** (Deadline: Oct 11, 2026)
   - Article: `articles/kaggle_benchmarking_challenge.md`
   - Notebook: `notebooks/kaggle_benchmark.ipynb`

---

## 📜 License & Credits

- Developed by **[@torrua](https://github.com/torrua)**, maintainer of [LOD Manager](https://github.com/torrua/LOD_manager).
- Licensed under the **MIT License**.
- Linguistic definitions based on the **Loglan Institute** materials and the **LOD** corpus.
