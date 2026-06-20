import streamlit as st

from frontend.utils import api_client


@st.cache_data(ttl=60)
def _load_patients() -> list[dict]:
    try:
        return api_client.get_patients()
    except Exception:
        return []


def render_patient_selector(key: str = "selected_patient_id") -> int | None:
    patients = _load_patients()

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

    if not patients:
        st.sidebar.error("Cannot reach API.")
        st.sidebar.code("uvicorn backend.main:app --reload")
        return None

    st.sidebar.markdown(
        f"<div style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:0.5px;color:#475569;margin-bottom:6px'>"
        f"Select Patient ({len(patients)} loaded)</div>",
        unsafe_allow_html=True,
    )

    options = {
        f"#{p['subject_id']} · {p.get('gender','?')} · Age {p.get('age','?')}": p["subject_id"]
        for p in patients
    }

    selected_label = st.sidebar.selectbox(
        "patient",
        options=list(options.keys()),
        key=key,
        label_visibility="collapsed",
    )

    pid = options[selected_label]

    # Mini patient card in sidebar
    p = next((x for x in patients if x["subject_id"] == pid), None)
    if p:
        alive_color = "#10b981" if p.get("alive") else "#94a3b8"
        alive_text  = "Alive" if p.get("alive") else "Deceased"
        st.sidebar.markdown(
            f"""
            <div style="background:#1e293b;border-radius:10px;padding:0.75rem;margin-top:0.5rem">
                <div style="font-size:0.78rem;font-weight:700;color:#e2e8f0">
                    Patient {p['subject_id']}
                </div>
                <div style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap">
                    <span style="font-size:0.7rem;color:#94a3b8">
                        Gender: <b style="color:#cbd5e1">{p.get('gender','—')}</b>
                    </span>
                    <span style="font-size:0.7rem;color:#94a3b8">
                        Age: <b style="color:#cbd5e1">{p.get('age','—')}</b>
                    </span>
                </div>
                <div style="margin-top:6px;display:flex;align-items:center;gap:5px">
                    <div style="width:6px;height:6px;border-radius:50%;
                                background:{alive_color}"></div>
                    <span style="font-size:0.7rem;color:{alive_color};font-weight:600">
                        {alive_text}
                    </span>
                    <span style="font-size:0.7rem;color:#475569;margin-left:auto">
                        {p.get('admission_count', 0)} admission(s)
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return pid
