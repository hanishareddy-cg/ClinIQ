import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from frontend.components.answer_card import render_answer
from frontend.components.patient_selector import render_patient_selector
from frontend.utils import api_client

st.set_page_config(page_title="Query Assistant · ClinIQ", page_icon="💬", layout="wide")

# ── Sidebar: patient selector ──────────────────────────────────────────────
patient_id = render_patient_selector(key="qa_patient_id")

# ── Session state ──────────────────────────────────────────────────────────
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []  # list of {question, response}

# ── Main area ──────────────────────────────────────────────────────────────
st.title("💬 Query Assistant")

if patient_id is None:
    st.info("Select a patient from the sidebar to get started.")
    st.stop()

# Show recent history (last 3 Q&As)
for item in st.session_state.qa_history[-3:]:
    with st.chat_message("user"):
        st.markdown(item["question"])
    render_answer(item["response"]["answer"], item["response"].get("citations", []))
    with st.expander("Retrieval details", expanded=False):
        stats = item["response"].get("retrieval_stats", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Latency", f"{stats.get('latency_ms', '—')} ms")
        c2.metric("Tokens used", stats.get("tokens_used", "—"))
        c3.metric("PG facts", stats.get("postgres_facts_retrieved", "—"))
        c4.metric("ES notes", stats.get("es_notes_retrieved", "—"))
        st.caption(f"Query type: {', '.join(item['response'].get('query_type', []))}")

st.divider()

# ── Query input ────────────────────────────────────────────────────────────
EXAMPLE_QUESTIONS = [
    "What are the most recent creatinine values?",
    "What medications is this patient currently on?",
    "Does this patient have a history of diabetes or hypertension?",
    "What did the discharge summary say about kidney function?",
    "Summarize this patient's clinical history",
]

with st.form("query_form", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        question = st.text_input(
            "Ask about this patient",
            placeholder="e.g. What are the latest lab results?",
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("Ask", use_container_width=True, type="primary")

st.caption("Try: " + " · ".join(f"*{q}*" for q in EXAMPLE_QUESTIONS[:3]))

# ── Handle submission ──────────────────────────────────────────────────────
if submitted and question.strip():
    with st.spinner("Retrieving records and synthesizing answer..."):
        try:
            response = api_client.post_query(patient_id, question.strip())
            st.session_state.qa_history.append({"question": question.strip(), "response": response})
            st.rerun()
        except Exception as e:
            st.error(f"Query failed: {e}")

elif submitted and not question.strip():
    st.warning("Please enter a question.")

# ── Sidebar extras ─────────────────────────────────────────────────────────
if st.session_state.qa_history:
    st.sidebar.divider()
    st.sidebar.caption("**Recent questions**")
    for item in reversed(st.session_state.qa_history[-5:]):
        st.sidebar.caption(f"• {item['question'][:60]}{'…' if len(item['question']) > 60 else ''}")

    if st.sidebar.button("Clear history", use_container_width=True):
        st.session_state.qa_history = []
        st.rerun()
