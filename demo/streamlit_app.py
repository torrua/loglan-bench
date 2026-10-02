"""Interactive Streamlit Demo App for Loglan Bench."""

import json
import sqlite3
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DB_PATH, RESULTS_DIR, CHARTS_DIR, DATA_DIR, DEFAULT_MODEL
from src.retriever import LoglanRetriever
from src.assistant import LoglanAssistant

st.set_page_config(
    page_title="Loglan Bench — Grammar Assistant & Formal Language Benchmark",
    page_icon="📐",
    layout="wide"
)

st.title("📐 Loglan Bench")
st.caption("AI Grammar Assistant on Gemma 3 + LOD Corpus • Zero Syntactic Ambiguity Benchmark")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings & Model")
    selected_model = st.selectbox(
        "Inference Model",
        ["gemma-3-27b-it", "gemini-2.5-flash", "mock-gemma-3"],
        index=0
    )
    use_mock = st.checkbox("Offline / Mock Mode", value=(selected_model == "mock-gemma-3"))
    st.markdown("---")
    st.markdown(
        "**Loglan** is an artificial speakable language invented in 1955 based on predicate logic, "
        "engineered to possess **zero syntactic ambiguity**."
    )
    st.markdown("Maintainer: [@torrua](https://github.com/torrua)")

@st.cache_resource
def get_assistant(model: str, mock: bool):
    return LoglanAssistant(model_name=model, mock=mock)

@st.cache_resource
def get_retriever():
    return LoglanRetriever(db_path=str(DB_PATH))

assistant = get_assistant(selected_model, use_mock)
retriever = get_retriever()

tab_chat, tab_dict, tab_visualizer, tab_bench = st.tabs([
    "💬 Grammar Assistant",
    "📖 LOD Dictionary Explorer",
    "⚖️ Ambiguity Visualizer",
    "📊 Benchmark Leaderboard"
])

# =========================================================================
# TAB 1: Chat Assistant
# =========================================================================
with tab_chat:
    st.subheader("Ask Loglan Grammar Assistant")
    st.write("Answers are strictly grounded in the official LOD lexicon (10,000+ words) and grammar articles from loglan.org.")

    col_q1, col_q2, col_q3 = st.columns(3)
    sample_q = ""
    if col_q1.button("Slots of 'donsu'"):
        sample_q = "What are the argument slots of 'donsu'?"
    if col_q2.button("Pretty little girls' school"):
        sample_q = "How do I express 'pretty little girls' school' unambiguously in Loglan?"
    if col_q3.button("Translate to Loglan"):
        sample_q = "Translate 'Daddy gave a puppy to Jane' into Loglan."

    query = st.text_input("Enter your question:", value=sample_q, placeholder="e.g. How do argument slots work in 'proga'?")

    if st.button("Submit Question", type="primary") or sample_q:
        if query.strip():
            with st.spinner("Retrieving grounded linguistic context and querying Gemma..."):
                raw_context = retriever.retrieve_context(query)
                answer = assistant.ask(query)

            st.markdown("### Answer")
            st.markdown(answer)

            with st.expander("🔍 Inspect Grounded RAG Context (LOD & loglan.org)"):
                st.markdown(raw_context)

# =========================================================================
# TAB 2: Dictionary Explorer
# =========================================================================
with tab_dict:
    st.subheader("Loglan Online Dictionary (LOD) Search")
    search_term = st.text_input("Search word or keyword in LOD:", value="donsu")

    if search_term.strip():
        results = retriever.search_dictionary(search_term, limit=10)
        if results:
            for r in results:
                slots = r.get("slots") or ""
                code = r.get("grammar_code") or ""
                gram = f"[{slots}{code}]" if (slots or code) else ""
                with st.container():
                    st.markdown(f"#### **{r['name']}** `({r['type']})` {gram}")
                    st.markdown(f"**Definition**: {r['body']}")
                    if r.get("usage"):
                        st.markdown(f"*Usage pattern*: `{r['usage']}`")
                    if r.get("components"):
                        st.markdown(f"*Affixes/Components*: {', '.join(r['components'])}")
                    st.markdown("---")
        else:
            st.info(f"No dictionary entries found for '{search_term}'.")

# =========================================================================
# TAB 3: Ambiguity Visualizer
# =========================================================================
with tab_visualizer:
    st.subheader("Natural Language Syntactic Ambiguity vs Loglan Precision")
    st.write(
        "In natural languages like English, modifier scopes and prepositional attachments produce "
        "exponentially branching parse trees. In Loglan, explicit grouping particles remove all ambiguity."
    )

    examples = {
        "Pretty little girls' school": {
            "english_parses": [
                "[[[Pretty little] girls'] school] — school for unusually small girls",
                "[[Pretty [little girls']] school] — attractive school for little girls",
                "[Pretty [little [girls' school]]] — attractive, small school for girls",
                "[[Pretty little] [girls' school]] — pretty & little institution",
                "[[[Pretty] [little] girls'] school] — girls who are both pretty and small"
            ],
            "loglan_solution": "le bilti ge cmalo nirli ckela",
            "grouping": "(bilti (cmalo (nirli ckela)))",
            "explanation": "Particle 'ge' groups modifiers right-to-left, locking exactly one parse tree."
        },
        "I saw the man with the telescope": {
            "english_parses": [
                "[I saw [the man with the telescope]] — the man possessed the telescope (attributive)",
                "[[I saw the man] with the telescope] — telescope was used as instrument of seeing"
            ],
            "loglan_solution": "Mi pa vizka le mrenu liu le teletro",
            "grouping": "Predicate argument / case tag 'liu' (instrument)",
            "explanation": "Loglan separates possessive/modifier ('pe') from instrument tag ('liu')."
        },
        "Flying planes can be dangerous": {
            "english_parses": [
                "[Flying planes] can be dangerous — airplanes in flight (participial adjective)",
                "[Flying [planes]] can be dangerous — the act of piloting airplanes (gerund)"
            ],
            "loglan_solution": "Lepo volsi plano ga kanmo lepo kinsei",
            "grouping": "Nominalizer 'lepo' (event/gerund) vs 'le' (object/plane)",
            "explanation": "Events require the 'lepo' clause marker; objects use 'le'."
        }
    }

    choice = st.selectbox("Select classic ambiguity example:", list(examples.keys()))
    ex = examples[choice]

    col_en, col_lo = st.columns(2)
    with col_en:
        st.markdown("### 🇬🇧 English Ambiguities")
        st.markdown(f"**Phrase**: *\"{choice}\"*")
        st.markdown(f"**Identified Parses ({len(ex['english_parses'])} valid trees):**")
        for p in ex["english_parses"]:
            st.markdown(f"- {p}")

    with col_lo:
        st.markdown("### 📐 Loglan Zero-Ambiguity Form")
        st.markdown(f"**Expression**: `{ex['loglan_solution']}`")
        st.markdown(f"**Exact Syntax Tree**: `{ex['grouping']}`")
        st.success(f"**Disambiguation Rule**: {ex['explanation']}")

# =========================================================================
# TAB 4: Benchmark Leaderboard
# =========================================================================
with tab_bench:
    st.subheader("Formal Language Benchmark Results")
    st.write("Comparison of 4 LLMs evaluated on 60 ground-truth Loglan tasks.")

    summary_file = RESULTS_DIR / "summary.csv"
    if summary_file.exists():
        df_summary = pd.read_csv(summary_file)
        st.dataframe(df_summary, use_container_width=True)

    col_c1, col_c2 = st.columns(2)
    chart1 = CHARTS_DIR / "model_accuracy_comparison.png"
    chart2 = CHARTS_DIR / "radar_evaluation.png"

    if chart1.exists():
        with col_c1:
            st.image(str(chart1), caption="Overall & Category Accuracy across Models")
    if chart2.exists():
        with col_c2:
            st.image(str(chart2), caption="Linguistic Reasoning Capability Profile")
