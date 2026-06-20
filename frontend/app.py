import streamlit as st

st.set_page_config(
    page_title="ClinIQ",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏥 ClinIQ")
st.markdown("**Clinical Record Intelligence Platform**")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Query Assistant")
    st.markdown(
        "Ask natural language questions about a patient's labs, medications, "
        "diagnoses, and clinical notes. Every answer is cited with source evidence."
    )
    st.page_link("pages/1_Query_Assistant.py", label="Open Query Assistant →", icon="💬")

with col2:
    st.markdown("### Patient Explorer")
    st.markdown(
        "Browse structured patient records — demographics, diagnoses, medications, "
        "lab trends, and vital sign history."
    )
    st.page_link("pages/2_Patient_Explorer.py", label="Open Patient Explorer →", icon="🔍")

st.divider()
st.caption("Vectorless RAG · PostgreSQL + Elasticsearch · Claude API · FastAPI · Streamlit")
