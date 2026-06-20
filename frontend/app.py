import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from frontend.utils.api_client import is_api_healthy
from frontend.utils.styles import inject_css

st.set_page_config(
    page_title="ClinIQ — Clinical Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Sidebar branding ───────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="padding:1rem 0.5rem 0.5rem">
        <div style="font-size:1.4rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.5px">
            🏥 ClinIQ
        </div>
        <div style="font-size:0.75rem;color:#64748b;margin-top:2px">
            Clinical Intelligence Platform
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/1_Query_Assistant.py", label="Query Assistant", icon="💬")
st.sidebar.page_link("pages/2_Patient_Explorer.py", label="Patient Explorer", icon="🔍")

api_ok = is_api_healthy()
status_color = "#10b981" if api_ok else "#ef4444"
status_text  = "API Online" if api_ok else "API Offline"
st.sidebar.markdown(
    f"""
    <div style="margin-top:auto;padding:1rem 0.5rem 0.5rem">
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:#64748b">
            <div style="width:7px;height:7px;border-radius:50%;background:{status_color};
                        box-shadow:0 0 6px {status_color}"></div>
            {status_text}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Hero ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;padding:3rem 1rem 2rem">
        <div style="font-size:3rem;margin-bottom:0.5rem">🏥</div>
        <h1 style="font-size:2.6rem;font-weight:800;color:#0f172a;
                   letter-spacing:-1px;margin-bottom:0.5rem">
            ClinIQ
        </h1>
        <p style="font-size:1.1rem;color:#64748b;max-width:560px;
                  margin:0 auto 0.75rem;line-height:1.6">
            Natural language queries over patient clinical records.<br>
            Every answer cited. No hallucinations.
        </p>
        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:1rem">
            <span style="background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;
                         border-radius:20px;padding:3px 12px;font-size:0.75rem;font-weight:600">
                PostgreSQL
            </span>
            <span style="background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;
                         border-radius:20px;padding:3px 12px;font-size:0.75rem;font-weight:600">
                Elasticsearch BM25
            </span>
            <span style="background:#faf5ff;color:#6b21a8;border:1px solid #e9d5ff;
                         border-radius:20px;padding:3px 12px;font-size:0.75rem;font-weight:600">
                Llama 3.3 70B
            </span>
            <span style="background:#fff7ed;color:#9a3412;border:1px solid #fed7aa;
                         border-radius:20px;padding:3px 12px;font-size:0.75rem;font-weight:600">
                FastAPI
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Stats row ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
for col, num, label in [
    (c1, "150", "Patients"),
    (c2, "48,900+", "Lab Results"),
    (c3, "115", "Clinical Notes"),
    (c4, "7", "Query Types"),
]:
    col.markdown(
        f"""
        <div class="stat-card">
            <div class="num">{num}</div>
            <div class="lbl">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Feature cards ──────────────────────────────────────────────────────────
col_qa, col_pe = st.columns(2, gap="large")

with col_qa:
    st.markdown(
        """
        <div class="feature-card">
            <h3>💬 Query Assistant</h3>
            <p>
                Ask natural language questions about any patient's records.
                The pipeline classifies your intent, retrieves structured facts
                and free-text notes in parallel, reranks by clinical relevance,
                and synthesizes a cited answer.
            </p>
            <ul>
                <li>Lab trends &amp; abnormal flags</li>
                <li>Medication history and dosing</li>
                <li>Discharge summary insights</li>
                <li>Diagnosis and comorbidity queries</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/1_Query_Assistant.py", label="Open Query Assistant →", icon="💬")

with col_pe:
    st.markdown(
        """
        <div class="feature-card">
            <h3>🔍 Patient Explorer</h3>
            <p>
                Browse structured patient records interactively.
                View demographics, admission timeline, and full clinical history.
                Visualize lab trends and vital signs over time.
            </p>
            <ul>
                <li>Interactive lab trend charts</li>
                <li>Vital signs over time</li>
                <li>Full medication and diagnosis list</li>
                <li>Admission history and duration</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/2_Patient_Explorer.py", label="Open Patient Explorer →", icon="🔍")

st.divider()
st.markdown(
    "<p style='text-align:center;font-size:0.75rem;color:#94a3b8'>"
    "Vectorless RAG · No embeddings · Fully auditable retrieval"
    "</p>",
    unsafe_allow_html=True,
)
