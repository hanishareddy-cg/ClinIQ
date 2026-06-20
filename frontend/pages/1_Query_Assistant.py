import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from frontend.components.answer_card import render_answer
from frontend.components.patient_selector import render_patient_selector
from frontend.utils import api_client
from frontend.utils.styles import inject_css, page_header

st.set_page_config(page_title="Query Assistant · ClinIQ", page_icon="💬", layout="wide")
inject_css()

patient_id = render_patient_selector(key="qa_patient_id")

page_header("💬", "Query Assistant", "Ask anything about a patient's clinical records", badge="AI Powered")

if patient_id is None:
    st.info("Select a patient from the sidebar to get started.")
    st.stop()

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# ── Query history ──────────────────────────────────────────────────────────
for item in st.session_state.qa_history[-3:]:
    with st.chat_message("user"):
        st.markdown(item["question"])
    render_answer(item["response"]["answer"], item["response"].get("citations", []))

    stats = item["response"].get("retrieval_stats", {})
    qt = item["response"].get("query_type", [])
    pills = "".join(f'<span class="qtype-pill">{q}</span>' for q in qt)

    with st.expander("Retrieval details", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Latency",   f"{stats.get('latency_ms', '—')} ms")
        c2.metric("Tokens",    stats.get("tokens_used", "—"))
        c3.metric("PG facts",  stats.get("postgres_facts_retrieved", "—"))
        c4.metric("ES notes",  stats.get("es_notes_retrieved", "—"))
        if pills:
            st.markdown(
                f"<div style='margin-top:6px'>{pills}</div>",
                unsafe_allow_html=True,
            )

if st.session_state.qa_history:
    st.divider()

# ── Query input ────────────────────────────────────────────────────────────
EXAMPLES = [
    "What are the most recent creatinine values?",
    "What medications is this patient on?",
    "Does this patient have diabetes or hypertension?",
    "What did the discharge summary say about kidney function?",
    "Summarize this patient's clinical history",
]

with st.form("query_form", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        question = st.text_input(
            "question",
            placeholder="e.g. What are the latest lab results?",
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("Ask →", use_container_width=True, type="primary")

st.markdown(
    "<div style='font-size:0.78rem;color:#94a3b8;margin-top:0.25rem'>"
    "Try: " + " &nbsp;·&nbsp; ".join(f"<i>{q}</i>" for q in EXAMPLES[:3]) + "</div>",
    unsafe_allow_html=True,
)

# ── Handle submission ──────────────────────────────────────────────────────
if submitted and question.strip():
    with st.spinner("Retrieving records and synthesizing answer…"):
        try:
            response = api_client.post_query(patient_id, question.strip())
            st.session_state.qa_history.append({
                "question": question.strip(),
                "response": response,
            })
            st.rerun()
        except Exception as e:
            st.error(f"Query failed: {e}")
elif submitted:
    st.warning("Please enter a question.")

# ── Sidebar: recent questions ──────────────────────────────────────────────
if st.session_state.qa_history:
    st.sidebar.divider()
    st.sidebar.markdown(
        "<div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;color:#475569;margin-bottom:6px'>Recent Questions</div>",
        unsafe_allow_html=True,
    )
    for item in reversed(st.session_state.qa_history[-5:]):
        q = item["question"]
        st.sidebar.markdown(
            f"<div style='font-size:0.75rem;color:#94a3b8;padding:3px 0;"
            f"border-left:2px solid #1e293b;padding-left:8px;margin-bottom:4px'>"
            f"{q[:55]}{'…' if len(q) > 55 else ''}</div>",
            unsafe_allow_html=True,
        )
    if st.sidebar.button("Clear history", use_container_width=True):
        st.session_state.qa_history = []
        st.rerun()
