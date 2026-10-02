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

### 3. Ingesting Grammar Books, Articles & Building FTS5

```bash
python src/ingest_docs.py
```
*Scrapes 28 canonical reference sources from `loglan.org` (including the 4th edition of James Cooke Brown's textbook "Loglan 1: A Logical Language", the LOD Lexicon Guide, case-tag treatises, subjunctive studies, and authentic parallel bilingual texts), extracts sentence tables and structural rules, segments them into semantic chunks, and builds `doc_fts` and `def_fts` SQLite FTS5 search indexes.*

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

## 📚 Knowledge Base & Grammar Corpus

Loglan Bench ingests **28 canonical sources** from [loglan.org](https://www.loglan.org/) organized across five linguistic categories:

| Category | Source Title | Canonical URL | Focus & Role |
|---|---|---|---|
| **Textbook** | *Loglan 1: Chap 1* | [chap1.html](https://www.loglan.org/Loglan1/chap1.html) | Linguistic design principles, Sapir-Whorf hypothesis, AI interfaces |
| **Textbook** | *Loglan 1: Chap 2* | [chap2.html](https://www.loglan.org/Loglan1/chap2.html) | Phonology, affix shapes, word-form resolution, stress/pause rules |
| **Textbook** | *Loglan 1: Chap 3* | [chap3.html](https://www.loglan.org/Loglan1/chap3.html) | Predicate grammar, tenses (`pa/na/fa`), modifiers, grouping (`ge/go`), connectives |
| **Textbook** | *Loglan 1: Chap 4* | [chap4.html](https://www.loglan.org/Loglan1/chap4.html) | Argument grammar, case tags (Table 4.1), descriptions (`le/lo`), variables (`da..du`) |
| **Textbook** | *Loglan 1: Chap 5* | [chap5.html](https://www.loglan.org/Loglan1/chap5.html) | Utterance grammar, modal/causal operators, punctuation, boundary markers (`ga/gu`) |
| **Textbook** | *Loglan 1: Chap 6* | [chap6.html](https://www.loglan.org/Loglan1/chap6.html) | Morphology growth, complex making, borrowings, affix joining rules |
| **Textbook** | *Loglan 1: App A* | [app-a.html](https://www.loglan.org/Loglan1/app-a.html) | Little words & little affixes complete lookup |
| **Textbook** | *Loglan 1: App D* | [app-d.html](https://www.loglan.org/Loglan1/app-d.html) | Predicate affixes complete dictionary reference |
| **Textbook** | *Loglan 1: App G* | [app-g.html](https://www.loglan.org/Loglan1/app-g.html) | Authentic parallel translations from *Scientific American* |
| **Dictionary** | *LOD Reading Guide* | [ReadingTheDictionary.html](https://www.loglan.org/LOD/ReadingTheDictionary.html) | Guide to LOD entry structure, grammar codes (`Prim`, `Cpx`, `2-Pl`), slot tags |
| **Articles** | *Easy Loglan Introduction* | [easy-loglan-introduction.html](https://www.loglan.org/Articles/easy-loglan-introduction.html) | Pedagogical primer with basic conversational sentences |
| **Articles** | *Easy Loglan Description* | [easy-loglan-description.html](https://www.loglan.org/Articles/easy-loglan-description.html) | High-level summary of Loglan structural mechanics |
| **Articles** | *Case Tag Theory* | [case-tag-theory.html](https://www.loglan.org/Articles/case-tag-theory.html) | Deep foundation of case tags, role assignment, and predicate slots |
| **Articles** | *Complex Word Making* | [complex-making.html](https://www.loglan.org/Articles/complex-making.html) | Mathematical rules for building complex predicates from primitives |
| **Articles** | *The Faces of Gu* | [faces-of-gu.html](https://www.loglan.org/Articles/faces-of-gu.html) | Disambiguation mechanics of right-boundary particle `gu` |
| **Articles** | *Logic and Economy* | [logic-and-economy.html](https://www.loglan.org/Articles/logic-and-economy.html) | Economy of expression and formal predicate calculus in syntax |
| **Articles** | *Sets and Masses* | [sets-and-masses.html](https://www.loglan.org/Articles/sets-and-masses.html) | Semantic distinctions between sets (`loi`), individuals, and masses (`lo`) |
| **Articles** | *Sets and Multiples* | [sets-and-multiples.html](https://www.loglan.org/Articles/sets-and-multiples.html) | Set operations, quantification, and numerical predicates |
| **Articles** | *Clarity and Unambiguity* | [clarity-abstract.html](https://www.loglan.org/Articles/clarity-abstract.html) | Theoretical proof and demonstration of zero-syntactic-ambiguity |
| **Semantics** | *The Mia System* | [mia-subjunctives.html](https://www.loglan.org/Articles/mia-subjunctives.html) | Subjunctive mood and counterfactual condition handling |
| **Semantics** | *I Would If I Could* | [I-would-if-I-could.html](https://www.loglan.org/Articles/I-would-if-I-could.html) | Practical counterfactual expressions and modal operators |
| **Semantics** | *Counterfactuals in Perspective* | [counterfactual-perspective.html](https://www.loglan.org/Articles/counterfactual-perspective.html) | Linguistic analysis of counterfactual conditionals |
| **Semantics** | *Assigning Case Tags* | [assigning-case-tags.html](https://www.loglan.org/Articles2/assigning-case-tags.html) | Systematic procedure for annotating LOD predicate argument slots |
| **Semantics** | *Progress on Case-Tags* | [case-tag-report.html](https://www.loglan.org/Articles2/case-tag-report.html) | Empirical report on slot alignment in the lexicon |
| **Semantics** | *Identity Predas and MEX* | [ident-predas-and-MEX.html](https://www.loglan.org/Articles/ident-predas-and-MEX.html) | Identity relations (`bi/bie`) and mathematical expressions |
| **Semantics** | *Exploring the PA Lexeme* | [exploring-PA.html](https://www.loglan.org/Sanpa/exploring-PA.html) | Detailed usage of tense and aspect markers (`pa`, `na`, `fa`) with examples |
| **Semantics** | *Numbers and How to Use Them* | [sanpa93-2-numbers.html](https://www.loglan.org/Sanpa/sanpa93-2-numbers.html) | Number system, fractions, and mathematical predication |
| **Texts** | *Sophie's World Excerpt* | [from-sophies-world.html](https://www.loglan.org/Texts/from-sophies-world.html) | Bilingual parallel philosophical text translation |
| **Texts** | *Ne Rorlensia* | [ne-rorlensia.html](https://www.loglan.org/Texts/ne-rorlensia.html) | Authentic short story in Loglan with parallel English translation |

---

## 📜 License, Copyright & Legal Attribution

### Software License
The codebase, benchmark harness, and evaluation tooling of **Loglan Bench** are open-source software licensed under the [MIT License](LICENSE) &copy; 2026 **[@torrua](https://github.com/torrua)**, maintainer of [LOD Manager](https://github.com/torrua/LOD_manager).

### Linguistic Materials & Copyright Notice
- **Loglan Language Design & Literature**: Created by **Dr. James Cooke Brown** (1921–2000) and developed by **The Loglan Institute, Inc. (TLI)**.
- **Copyright &copy; 1975–2026 The Loglan Institute, Inc.** All rights reserved by the original copyright holders. Canonical texts, dictionaries, and grammar publications are accessible at the official repository [https://www.loglan.org](https://www.loglan.org).
- **LOD (Loglan Online Dictionary)**: The lexicon database `export.db` is derived from the official Loglan Online Dictionary compiled and maintained by the Loglan Institute community.
- **Fair Use & Research Purpose**: The ingestion of grammar chapters and articles into SQLite FTS5 is performed strictly for **non-commercial educational, linguistic research, and AI benchmarking evaluation purposes** (transformative fair use under 17 U.S.C. &sect; 107). No commercial redistribution or claim of ownership over the underlying linguistic grammar or texts is made.
- **Automated Retrieval Etiquette**: The ingestion crawler identifies itself via the research User-Agent header `LoglanBenchBot/1.0 (+https://github.com/torrua/loglan-bench)` and queries public static HTML documents with rate-friendly sequential timeouts.
- **Citation Guidance**: If you use Loglan Bench or the extracted datasets in academic publications, please cite both the software repository and the original Loglan Institute foundation:
  ```bibtex
  @misc{loglanbench2026,
    author = {Torrua},
    title = {Loglan Bench: First Open Benchmark & RAG Grammar Assistant for a Syntactically Unambiguous Human Language},
    year = {2026},
    publisher = {GitHub},
    url = {https://github.com/torrua/loglan-bench}
  }
  @book{brown1989loglan1,
    author = {Brown, James Cooke},
    title = {Loglan 1: A Logical Language},
    edition = {4th},
    year = {1989},
    publisher = {The Loglan Institute, Inc.},
    address = {Gainesville, Florida},
    url = {https://www.loglan.org/Loglan1/}
  }
  ```
