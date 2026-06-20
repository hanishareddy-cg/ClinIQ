import streamlit as st

from frontend.utils import api_client


@st.cache_data(ttl=60)
def _load_patients() -> list[dict]:
    try:
        return api_client.get_patients()
    except Exception:
        return []


def render_patient_selector(key: str = "selected_patient_id") -> int | None:
    """
    Renders a patient dropdown in the sidebar.
    Returns the selected patient_id, or None if none selected.
    """
    patients = _load_patients()

    if not patients:
        st.sidebar.error("Cannot reach API. Is the backend running?")
        st.sidebar.code("uvicorn backend.main:app --reload")
        return None

    options = {
        f"Patient {p['subject_id']} | {p.get('gender','?')} | Age {p.get('age','?')}": p["subject_id"]
        for p in patients
    }

    st.sidebar.markdown("### 🏥 ClinIQ")
    st.sidebar.caption(f"{len(patients)} patients loaded")
    st.sidebar.divider()

    selected_label = st.sidebar.selectbox(
        "Select patient",
        options=list(options.keys()),
        key=key,
    )

    return options[selected_label]
