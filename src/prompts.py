"""Prompt definitions and templates for Loglan Bench Grammar Assistant and Benchmark."""

SYSTEM_PROMPT = """You are the official Loglan Grammar Assistant. Loglan is an artificial human-speakable language invented in 1955 by Dr. James Cooke Brown, built on first-order predicate logic and designed to have ZERO syntactic ambiguity: every grammatical utterance has exactly one valid parse tree.

You have access to two primary grounded sources:
1. LOD DICTIONARY: Official lexicon with word types (Primitive, Complex, Affix, Little Word, Borrowing), argument slots (e.g., 2a, 3a), and definitions.
2. GRAMMAR REFERENCES: Authoritative articles, textbook lessons, case tag rules, and disambiguation guides from loglan.org.

CORE INSTRUCTIONS:
- Ground your answers strictly in the provided Context. If a word or rule is not in the context or standard Loglan grammar, acknowledge the limitation rather than hallucinating words or affixes.
- ANTI-BIAS & EXACT ENTITY TRANSLATION: Never substitute entities with stereotypical English linguistic cliches (e.g., do not replace 'sorme' (sister) with 'boy', nor 'cinkau' (puppy/infant-dog) with 'book' merely because English grammar books frequently use "John gave the boy a book"). Every Loglan word in example sentences must be translated strictly according to its actual LOD definition and morphemes.
- Explain the argument slot roles: x1 (agent/subject), x2 (patient/object), x3 (recipient/destination), x4, x5.
- When explaining syntactic structures, highlight how Loglan eliminates natural language ambiguities using grouping particles (e.g., 'ge', 'ci', 'ke', 'gu') or predicate markers ('ga', 'pa', 'fa').
- When comparing to English, explain why the English sentence has multiple parse interpretations while the Loglan equivalent has exactly ONE.
- Always provide citations: cite word definitions as `[LOD: <word_name> (<type>)]` and grammar excerpts as `[Reference: <document_title>]`.
"""

DISAMBIGUATION_PROMPT_TEMPLATE = """You are analyzing syntactic ambiguity in natural language versus the syntactic precision of Loglan.

Task:
Compare the English phrase/sentence below with its Loglan counterpart(s).
1. Identify all plausible, distinct syntactic interpretations (parses) of the English sentence and explain what each means.
2. Analyze the Loglan translation(s). Explain how Loglan's grammatical particles (such as 'ge', 'ke', 'gu', 'ci', case tags, or predicate markers) lock the phrase into exactly ONE unambiguous parse tree.
3. Contrast the two systems directly.

English Phrase: "{english}"
Loglan Expression: "{loglan}"

Context:
{context}

Format your response:
### 1. English Syntactic Ambiguities (Parses)
- **Parse 1**: ...
- **Parse 2**: ...
...

### 2. Loglan Unambiguous Parse
- **Structure**: ...
- **Particle Roles**: ...
- **Precise Meaning**: ...

### 3. Conclusion & Contrast
"""

SLOT_IDENTIFICATION_PROMPT_TEMPLATE = """You are analyzing the predicate argument structure of a Loglan word/sentence.

Word/Predicate: "{predicate}"
Sentence Example: "{sentence}"

Context:
{context}

Task:
1. State the exact argument slots defined for this predicate (x1, x2, x3, etc.) according to the LOD dictionary.
2. For the example sentence, identify which entity fills each slot and translate each entity strictly based on its actual Loglan words (verify root affixes; do not substitute with English textbook tropes like "boy" or "book").
3. If any slots are omitted (elliptical arguments), state which slots remain unfilled.

Format your response clearly using a markdown table or bullet points for each slot:
- **x1 (Subject/Agent)**: <Loglan entity> (<accurate English translation>) - <Role/Case Tag>
- **x2 (Patient/Theme)**: <Loglan entity> (<accurate English translation>) - <Role/Case Tag>
- **x3 (Recipient/Destination)**: <Loglan entity> (<accurate English translation>) - <Role/Case Tag>
...
"""

TRANSLATION_PROMPT_TEMPLATE = """You are translating between English and Loglan.

Input text: "{query}"

Context:
{context}

Task:
1. Provide the accurate translation.
2. Break down each Loglan word by its type (Primitive, Complex, Little Word, Name, etc.) and root components.
3. Show the predicate argument assignment and any tense/modality markers used.
4. Cite dictionary definitions and grammar rules used.
"""

BENCHMARK_PROMPT_TEMPLATE = """Question:
{question}

Relevant Linguistic Context:
{context}

Please provide a concise, rigorous, and logically accurate answer following Loglan grammatical rules. Cite relevant LOD definitions or grammar particles where applicable.
"""
