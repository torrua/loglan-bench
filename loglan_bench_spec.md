# PROJECT: Loglan Bench

> AI-ассистент по грамматике Loglan на Gemma + бенчмарк: как LLM справляются с формальным языком vs. естественным.

---

## 1. Контекст: что уже есть

Автор (GitHub: [torrua](https://github.com/torrua)) — maintainer **[LOD Manager](https://github.com/torrua/LOD_manager)**, десктопного редактора словаря Loglan (Tauri v2 + Svelte 5 + Rust + SQLite/FTS5).

**Loglan** — искусственный человеческий язык, созданный в 1955 году на основе логики предикатов первого порядка. Ключевое свойство: **нулевая синтаксическая неоднозначность** — каждое грамматически правильное предложение имеет ровно один разбор.

**LOD** (Loglan Online Dictionary) — корпус языка: ~10 000 слов, определения с аргументными слотами (`B is a «program» for/to do P on system F written by K`), типы слов (Primitive, Complex, Affix, Little Word, Borrowing), ключевые слова в формате `«keyword»`. Хранится в SQLite-базе `export.db`.

Уже опубликована статья на DEV: [Saving a 1950s Artificial Language for the Age of Artificial Intelligence](https://dev.to/torrua/building-lod-manager-an-open-source-desktop-dictionary-editor-with-tauri-v2-svelte-5-and-rust-4h5m). Тезис статьи: искусственные языки и искусственный интеллект решают одну задачу с разных сторон. Новый проект **доказывает этот тезис данными**.

---

## 2. Что строим

### Продукт: Loglan Grammar Assistant

CLI-инструмент (Python), который:

1. Принимает вопрос на английском:
   - *"How do I say 'pretty little girls' school' unambiguously in Loglan?"*
   - *"What are the argument slots of 'donsu'?"*
   - *"Translate 'La Djan donsu le bukcu la Maris' to English"*
2. Ищет по корпусу LOD (SQLite) — релевантные слова, определения, примеры.
3. Формирует промпт с контекстом из корпуса и отправляет в **Gemma** (open-weight модель от Google).
4. Возвращает ответ с цитатами из словаря.

### Побочный продукт: LLM Benchmark

Прогоняем набор тестовых задач (parsing, slot identification, disambiguation) через 4 модели. Публикуем как Kaggle notebook + dataset.

### Почему это «для друга»

> *«Мой друг [имя/ник] — один из активных участников сообщества Loglan. Когда в сообществе возникает спор о значении слова или правильности конструкции, он вручную ищет по корпусу, разбирает грамматику и объясняет новичкам. Это занимает часы. Я построил ему AI-ассистента, который знает весь словарь и отвечает на вопросы мгновенно — и заодно обнаружил, что Loglan работает как идеальный бенчмарк для LLM.»*

Если «друг» — это сам автор, тоже валидно: *"I'm the maintainer, and I built this for myself — because explaining Loglan grammar to newcomers takes hours I don't have."*

---

## 3. Два челленджа

### Челлендж A: Hacktoberfest Weekend Challenge

| Параметр | Значение |
|---|---|
| **Название** | Hacktoberfest Weekend Challenge: Build for a Friend |
| **Промпт** | Build something with **open-source AI at its core** |
| **Тема** | **"Build for a Friend"** — решить реальную проблему для конкретного человека |
| **Дедлайн** | **5 октября 2026, 06:59 UTC** (09:59 по Москве) |
| **Теги** | `#hf26challenge`, `#hacktoberfest`, `#ai`, `#opensource` |
| **Требования** | Статья на DEV + демо (deployed link или видео) + ссылка на код |
| **Призы** | \$250 overall, \$200 Best Use of Gemma, \$100+ partner categories |
| **Страница** | https://dev.to/challenges/hacktoberfest-weekend-2026-10-01 |

**Критерии судейства (по приоритету):**
1. **Writing Quality** (высший вес) — объяснить «why open-source AI», рассказать историю
2. **Relevance to Prompt + Theme** — open-source AI + «для друга»
3. **Creativity** — оригинальность подхода
4. **Technical Execution** — работающий проект
5. **Partner Technology** (бонус) — Gemma

**Как мы закрываем «open-source AI at its core»:**
- Gemma — open-weight модель от Google, MIT-подобная лицензия
- Корпус LOD — open-source данные
- Весь код — MIT-лицензия
- **Можно запустить полностью локально**, без облака и API
- В статье объяснить: «Unlike closed APIs, the model can be fine-tuned on Loglan grammar. The dictionary data never leaves the machine.»

### Челлендж B: Kaggle Benchmarking Challenge

| Параметр | Значение |
|---|---|
| **Промпт** | Построить **бенчмарк на Kaggle**, сравнить модели |
| **Дедлайн** | **11 октября 2026, 23:59 PDT** |
| **Теги** | `#kagglechallenge`, `#devchallenge`, `#ai`, `#machinelearning` |
| **Требования** | Статья на DEV по шаблону + ссылка на Kaggle notebook |
| **Призы** | \$500 (один из 5 победителей) |
| **Лимит** | 1 сабмишн на участника |
| **Страница** | https://dev.to/challenges/kaggle-2026-09-23 |

**Шаблон статьи (обязательный):**
```markdown
*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

## What I Benchmarked
## Models Tested
## Findings & Real-World Meaning
## Where can we see it?
```

---

## 4. Техническая архитектура

```
┌──────────────────────────────────────────────┐
│            loglan-bench CLI (Python)          │
│                                              │
│  1. Query parser (argparse / Streamlit)      │
│  2. RAG retriever (SQLite → context)         │
│  3. Prompt builder (system + context + query)│
│  4. Model caller (google-genai SDK)          │
│  5. Response formatter (citations)           │
└─────────────────────┬────────────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │     LOD SQLite (export.db) │
        │                           │
        │  words: id, name, type    │
        │  definitions: body, usage │
        │  keys: word, language     │
        │  connect_words: parent_id,│
        │    child_id               │
        └─────────────┬─────────────┘
                      │ контекст (определения,
                      │ примеры, связи)
        ┌─────────────▼─────────────┐
        │      LLM (Gemma 3)        │
        │                           │
        │  google-genai SDK         │
        │  или ollama (локально)    │
        │  или Kaggle GPU notebook  │
        └───────────────────────────┘
```

### Зависимости (Python)

```
google-genai          # Gemma API (primary)
ollama                # Local inference (optional)
openai                # GPT-4o-mini for benchmark comparison
anthropic             # Claude Haiku for benchmark comparison
sqlite3               # Built-in, for LOD corpus
beautifulsoup4        # Scraping loglan.org articles
pandas                # Dataset and results
matplotlib / seaborn  # Visualizations
streamlit             # Optional: simple web UI for demo
```

### Корпус грамматических документов

Словарь LOD содержит только слова и определения — но для ассистента, который объясняет грамматику, нужны учебные материалы: как работают частицы, правила построения предложений, разборы примеров.

**Источники (приоритет по полезности):**

| Источник | Что даёт | URL |
|---|---|---|
| **Easy Loglan Introduction** | Базовая грамматика, 11 уроков с примерами (attitudinals, predicates, tense, connectives, case tags) | https://www.loglan.org/Articles/easy-loglan-introduction.html |
| **Статьи с loglan.org** | Продвинутая грамматика, парсинг, фонология | https://www.loglan.org/Articles/ |
| **Loglan 1** (учебник Брауна) | Полная грамматика, глоссарий, история | Если доступен в digital |
| **La Logli** (журнал) | Примеры использования, дискуссии | Если доступен |
| **README / wiki LOD Manager** | Описание схемы данных, типов слов | https://github.com/torrua/LOD_manager |

**Схема хранения:**

```sql
-- Документы разбиты на чанки ~500 слов
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,          -- "Easy Loglan: Lesson 3 — Tense"
    source_url TEXT,              -- URL источника
    chunk TEXT NOT NULL,          -- текст чанка
    chunk_index INTEGER NOT NULL, -- порядковый номер в документе
    UNIQUE(source_url, chunk_index)
);

-- FTS5 индекс для полнотекстового поиска по документам
CREATE VIRTUAL TABLE doc_fts USING fts5(
    chunk, title,
    content='documents',
    tokenize='unicode61 remove_diacritics 1'
);
```

**Скрипт инъекции (`ingest_docs.py`):**

```python
import requests
from bs4 import BeautifulSoup
import sqlite3
import textwrap

SOURCES = [
    ("Easy Loglan Introduction",
     "https://www.loglan.org/Articles/easy-loglan-introduction.html"),
    # добавить другие статьи по мере нахождения
]

def scrape_and_chunk(url: str, chunk_size: int = 500) -> list[str]:
    """Fetch HTML, extract text, split into chunks."""
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    # Split by paragraphs, then group into chunks of ~chunk_size words
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], []
    word_count = 0
    for para in paragraphs:
        words = len(para.split())
        if word_count + words > chunk_size and current:
            chunks.append("\n".join(current))
            current, word_count = [], 0
        current.append(para)
        word_count += words
    if current:
        chunks.append("\n".join(current))
    return chunks

def ingest(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source_url TEXT,
        chunk TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        UNIQUE(source_url, chunk_index)
    )""")
    conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS doc_fts
        USING fts5(chunk, title, content='documents',
        tokenize='unicode61 remove_diacritics 1')""")

    for title, url in SOURCES:
        chunks = scrape_and_chunk(url)
        for i, chunk in enumerate(chunks):
            conn.execute(
                "INSERT OR IGNORE INTO documents (title, source_url, chunk, chunk_index) VALUES (?,?,?,?)",
                (title, url, chunk, i))
    conn.execute("INSERT INTO doc_fts(doc_fts) VALUES('rebuild')")
    conn.commit()
```

**Влияние на проект:**
- **Ассистент** → грамматические объяснения + примеры, а не только словарные определения
- **Бенчмарк** → честнее: модель получает реальный учебный контекст, тестируем reasoning, а не знание экзотики
- **«For a friend»** → «я собрал все учебники и статьи в одну базу, чтобы ему не искать по десяткам страниц»

### RAG-процесс (как ищем по корпусу)

Поиск двухуровневый: сначала словарь (слова + определения), потом грамматические документы. Оба контекста идут в промпт.

```python
def retrieve_context(db_path: str, query: str, top_k: int = 5) -> str:
    """Search LOD dictionary + grammar documents."""
    conn = sqlite3.connect(db_path)
    sections = []

    # --- 1. Dictionary: words + definitions ---
    dict_results = conn.execute("""
        SELECT w.name, w.type, d.body, d.usage, d.grammar_code, d.slots
        FROM def_fts f
        JOIN definitions d ON d.rowid = f.rowid
        JOIN words w ON w.id = d.word_id
        WHERE def_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, top_k)).fetchall()

    if not dict_results:
        dict_results = conn.execute("""
            SELECT w.name, w.type, d.body, d.usage, d.grammar_code, d.slots
            FROM words w
            JOIN definitions d ON d.word_id = w.id
            WHERE w.name LIKE ? OR d.body LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", top_k)).fetchall()

    if dict_results:
        lines = []
        for name, wtype, body, usage, grammar, slots in dict_results:
            grammar_str = f"{slots}{grammar}" if slots and grammar else ""
            line = f"- **{name}** ({wtype}) [{grammar_str}]: {body}"
            if usage:
                line += f" | Usage: {usage}"
            lines.append(line)
        sections.append("### Dictionary Entries\n" + "\n".join(lines))

    # --- 2. Grammar documents ---
    doc_results = conn.execute("""
        SELECT title, chunk
        FROM doc_fts
        WHERE doc_fts MATCH ?
        ORDER BY rank
        LIMIT 3
    """, (query,)).fetchall()

    if doc_results:
        lines = [f"**{title}:**\n{chunk}" for title, chunk in doc_results]
        sections.append("### Grammar Reference\n" + "\n\n".join(lines))

    return "\n\n".join(sections) if sections else "No relevant context found."
```

### Системный промпт для ассистента

```python
SYSTEM_PROMPT = """You are a Loglan grammar assistant. Loglan is an artificial
human-speakable language based on first-order predicate logic, designed to have
zero syntactic ambiguity. Every grammatical sentence has exactly one parse tree.

You have two sources of knowledge:
1. DICTIONARY — word entries with definitions, argument slots, and keywords
2. GRAMMAR REFERENCE — excerpts from Loglan textbooks and articles

Answer using ONLY the context provided below. If the context doesn't contain
enough information, say so honestly — do not invent Loglan words or grammar.

Key Loglan concepts:
- Predicates have fixed argument slots: x1 (agent), x2 (patient), x3...
- Grammar particles (ge, ci, ke, etc.) control modifier binding
- Word types: Primitive (Prim), Complex (Cpx), Affix (Afx), Little Word (LW), Borrowing (Bor)
- «keyword» markers inside definitions indicate indexed terms
- Zero syntactic ambiguity: one sentence = one parse tree

When showing Loglan examples, always explain the parse structure.
When comparing to English, highlight where English is ambiguous and Loglan is not.
Cite dictionary definitions with word name and type.
Cite grammar references with document title."""
```

---

## 5. Датасет для бенчмарка

### Формат (CSV / JSON)

```json
{
  "id": 1,
  "category": "disambiguation",
  "english": "Pretty little girls' school",
  "loglan": "le cmalo nirli ckela ge gudbi",
  "task": "List all syntactically valid parses of this phrase",
  "expected_english_parses": 5,
  "expected_loglan_parses": 1,
  "gold_answer": "..."
}
```

### Три категории тестов

#### A. Disambiguation (20–30 примеров)

Цель: может ли модель определить все разборы неоднозначной английской фразы и единственный разбор Loglan-эквивалента?

| English (ambiguous) | # parses | Loglan (unambiguous) | # parses |
|---|---|---|---|
| Pretty little girls' school | 5+ | [5 разных конструкций с ge/ci] | 1 each |
| I saw the man with the telescope | 2 | [2 разные конструкции] | 1 each |
| Flying planes can be dangerous | 2 | [2 разные конструкции] | 1 each |
| The chicken is ready to eat | 2 | [2 разные конструкции] | 1 each |

Источники: классические примеры из лингвистики + [loglan.org](https://loglan.org)

#### B. Predicate Slot Identification (20–30 примеров)

Цель: правильно ли модель определяет аргументные роли (кто, что, кому)?

```
Loglan definition: "B is a «program» for/to do P on system F written by K"
Q: "If I say 'le proga', who is B, P, F, K?"
Expected: B=the program, P=what it does, F=the system, K=the author
```

Берём 20–30 слов из LOD с разным количеством слотов (1–5 аргументов).

#### C. Translation Consistency (20–30 примеров)

Цель: даёт ли модель одинаковый ответ при 5 повторных прогонах?

```
Q: "Translate 'La Djan donsu le bukcu la Maris' to English"
Run 5 times, measure consistency (exact match / semantic match)
```

### Метрики

| Metric | Описание | Как считаем |
|---|---|---|
| **Parse Accuracy** | % правильных разборов | correct / total |
| **Parse Count Accuracy** | Угадала ли модель количество парсов | exact match |
| **Slot Accuracy** | Правильно ли определены аргументные роли | exact match per slot |
| **Consistency Score** | Одинаковый ли ответ при 5 прогонах | (matching pairs) / (total pairs) |
| **Hallucination Rate** | Придумала ли модель несуществующие слова/парсы | manual check + auto-check vs LOD |
| **Token Cost** | Средние затраты на задачу | sum(input + output tokens) |

---

## 6. Модели

| Модель | Тип | Доступ | Зачем |
|---|---|---|---|
| **Gemma 3 (27B или 12B)** | Open-weight | google-genai SDK / Kaggle GPU | Основная. Категория "Best Use of Gemma" |
| **Llama 3.1 8B** | Open-weight | Ollama / Together AI | Сравнение open vs open |
| **GPT-4o-mini** | Closed | OpenAI API | Контраст: closed baseline |
| **Claude 3.5 Haiku** | Closed | Anthropic API | Ещё один closed для валидации |

Для Hacktoberfest **Gemma — центральная модель**. В статье объяснить, почему open-weight лучше для этой задачи:
- Можно запустить локально (данные словаря не уходят в облако)
- Можно fine-tune на грамматике Loglan (follow-up проект)
- Воспроизводимость: любой может повторить бенчмарк

---

## 7. Структура репозитория

```
loglan-bench/
├── README.md
├── LICENSE (MIT)
├── requirements.txt
├── data/
│   ├── export.db              # LOD corpus (SQLite)
│   └── benchmark_dataset.json # 50-100 test cases
├── src/
│   ├── assistant.py           # RAG assistant (CLI)
│   ├── retriever.py           # SQLite → context (dictionary + docs)
│   ├── ingest_docs.py         # Scrape loglan.org → documents table
│   ├── prompts.py             # System prompts
│   ├── benchmark.py           # Run all models, collect results
│   └── evaluate.py            # Compute metrics
├── notebooks/
│   └── kaggle_benchmark.ipynb # Kaggle submission notebook
├── results/
│   ├── raw/                   # Raw model outputs
│   └── summary.csv            # Aggregated metrics
└── demo/
    └── streamlit_app.py       # Optional web demo
```

---

## 8. Пошаговый план реализации

### День 1 (2 октября) — Фундамент

- [ ] Создать репозиторий `loglan-bench` на GitHub
- [ ] Скопировать `export.db` из LOD Manager (или сгенерировать)
- [ ] Написать `ingest_docs.py` — скрейпинг статей с loglan.org → таблица `documents` + FTS5
- [ ] Запустить инъекцию: Easy Loglan Introduction + другие доступные статьи
- [ ] Написать `retriever.py` — двухуровневый RAG (словарь + документы)
- [ ] Написать `prompts.py` — системный промпт
- [ ] Написать `assistant.py` — CLI: вопрос → контекст → Gemma → ответ
- [ ] Проверить, что ассистент работает на 5–10 тестовых вопросах
- [ ] Начать собирать датасет: 20–30 пар для категории Disambiguation

### День 2 (3 октября) — Бенчмарк

- [ ] Дособрать датасет: категории B (slots) и C (translation)
- [ ] Написать `benchmark.py` — прогон через 4 модели
- [ ] Написать `evaluate.py` — подсчёт метрик
- [ ] Прогнать бенчмарк, собрать результаты
- [ ] Сделать визуализации (bar charts: accuracy по моделям, heatmaps)
- [ ] Записать демо-видео или задеплоить Streamlit

### День 3 (4 октября) — Статьи

- [ ] Написать Hacktoberfest-статью (нарратив «для друга»)
- [ ] Написать Kaggle-статью (шаблон What I Benchmarked)
- [ ] Загрузить notebook + dataset на Kaggle
- [ ] Сабмитнуть обе статьи на DEV
- [ ] Проверить теги, ссылки, демо

> **Hacktoberfest дедлайн: 5 октября 06:59 UTC (09:59 MSK)**
> **Kaggle дедлайн: 11 октября 23:59 PDT** — можно доработать после weekend

---

## 9. Outline статьи для Hacktoberfest

**Заголовок:** *"My Friend Can't Explain Loglan Grammar Fast Enough — So I Built Him an AI That Speaks a 1950s Artificial Language"*

**Теги:** `hf26challenge`, `hacktoberfest`, `ai`, `opensource`

```markdown
*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## The Friend
[Кто он, что делает в Loglan community, в чём проблема.
Конкретные детали: сколько лет в сообществе, что именно делает]

## The Problem
[Ручной разбор грамматики, объяснения новичкам, часы на поиск по корпусу.
Учебники разбросаны по десяткам страниц loglan.org, нет единого источника.
Словарь содержит определения, но не объяснения грамматики]

## The Build
[RAG over LOD corpus + grammar documents + Gemma:
1. Собрал словарь (10 000 слов) + учебные материалы (статьи с loglan.org) в одну SQLite базу
2. FTS5 двухуровневый поиск: сначала по словарю, потом по грамматическим документам
3. Контекст → промпт → Gemma → ответ с цитатами
Показать архитектуру, 1-2 примера вопросов и ответов]

## Why Open-Source AI
[Gemma: локально, fine-tune, данные не уходят, воспроизводимость.
«Unlike closed APIs, Gemma can be fine-tuned on Loglan grammar.
The dictionary data never leaves the machine.
Anyone can reproduce the benchmark.»]

## The Surprise: A Formal Language is the Perfect LLM Benchmark
[Каждое предложение = ground truth, нулевая неоднозначность.
«Pretty little girls' school» — 5 парсов в English, 1 в Loglan.
Это готовый eval corpus без ручной разметки]

## Results
[Графики: Gemma vs others, accuracy, consistency, hallucinations.
Таблица метрик. Ключевые findings]

## Try It Yourself
[Ссылка на GitHub repo, демо, Kaggle notebook]
```

---

## 10. Outline статьи для Kaggle

**Заголовок:** *"Can LLMs Parse a Language With Zero Ambiguity? Benchmarking 4 Models on Loglan"*

**Теги:** `kagglechallenge`, `devchallenge`, `ai`, `machinelearning`

```markdown
*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

## What I Benchmarked
Can LLMs correctly parse sentences in Loglan — an artificial language
with zero syntactic ambiguity — better than equivalent English sentences?
Three test categories: disambiguation, predicate slot identification,
and translation consistency.

## Models Tested
- Gemma 3 27B (open-weight, Google)
- Llama 3.1 8B (open-weight, Meta)
- GPT-4o-mini (closed, OpenAI)
- Claude 3.5 Haiku (closed, Anthropic)

## Findings & Real-World Meaning
[Таблицы и графики с метриками]
[Ключевые findings: где формальный язык помогает, где нет]
[Практический вывод для structured output / DSL design]

## Where can we see it?
- Kaggle notebook: [ссылка]
- Dataset: [ссылка]
- Full repo: [ссылка на GitHub]
```

---

## 11. Полезные ссылки

| Ресурс | URL |
|---|---|
| LOD Manager repo | https://github.com/torrua/LOD_manager |
| Loglan Institute | https://loglan.org |
| Easy Loglan Introduction | https://www.loglan.org/Articles/easy-loglan-introduction.html |
| Gemma on Kaggle | https://www.kaggle.com/models/google/gemma |
| google-genai SDK docs | https://ai.google.dev/gemini-api/docs |
| Hacktoberfest Weekend Challenge | https://dev.to/challenges/hacktoberfest-weekend-2026-10-01 |
| Kaggle Benchmarking Challenge | https://dev.to/challenges/kaggle-2026-09-23 |
| Hacktoberfest 2026 overview | https://dev.to/devteam/hacktoberfest-2026-dev-challenges-five-challenges-one-prompt-a-new-theme-every-week-1e54 |
| Опубликованная статья (LOD Manager) | https://dev.to/torrua/building-lod-manager-an-open-source-desktop-dictionary-editor-with-tauri-v2-svelte-5-and-rust-4h5m |

---

## 12. Схема базы данных LOD (export.db)

Ключевые таблицы для RAG:

```sql
-- Слова
words: id, name, type, origin, origin_x, "match", rank, year, notes,
       id_old, "TID_old", event_start, event_end

-- Определения (главный источник контекста)
definitions: id, word_id, position, body, usage, grammar_code, slots,
             case_tags, language, notes
-- body содержит «keyword» маркеры: "B is a «program» for/to do P"
-- slots + grammar_code = полная грамматическая строка (напр. "2a")

-- Ключевые слова (bidirectional search)
keys: id, word, language

-- Связи между словами (дериваты, комплексы)
connect_words: parent_id, child_id

-- Типы слов
types: id, type, type_x, "group", parentable, description

-- FTS5 индекс (если есть)
def_fts: body, usage, notes (virtual table, content='definitions')
```
