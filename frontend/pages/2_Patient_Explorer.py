import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

from frontend.components.patient_selector import render_patient_selector
from frontend.utils import api_client
from frontend.utils.formatting import fmt_date, fmt_datetime

st.set_page_config(page_title="Patient Explorer · ClinIQ", page_icon="🔍", layout="wide")

# ── Sidebar ────────────────────────────────────────────────────────────────
patient_id = render_patient_selector(key="explorer_patient_id")

st.title("🔍 Patient Explorer")

if patient_id is None:
    st.info("Select a patient from the sidebar.")
    st.stop()

# ── Load patient detail ────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_detail(pid: int) -> dict:
    return api_client.get_patient_detail(pid)

@st.cache_data(ttl=30)
def load_labs(pid: int) -> list[dict]:
    return api_client.get_patient_labs(pid)

@st.cache_data(ttl=30)
def load_vitals(pid: int) -> list[dict]:
    return api_client.get_patient_vitals(pid)

try:
    detail = load_detail(patient_id)
except Exception as e:
    st.error(f"Could not load patient: {e}")
    st.stop()

# ── Demographics row ───────────────────────────────────────────────────────
st.subheader(f"Patient {detail['subject_id']}")
d1, d2, d3, d4 = st.columns(4)
d1.metric("Gender",       detail.get("gender") or "—")
d2.metric("Age",          detail.get("age") or "—")
d3.metric("Status",       "Alive" if detail.get("alive") else "Deceased")
d4.metric("Admissions",   len(detail.get("admissions", [])))

st.divider()

# ── Three column overview ──────────────────────────────────────────────────
col_dx, col_med, col_adm = st.columns(3)

with col_dx:
    st.markdown("**Diagnoses**")
    diagnoses = detail.get("diagnoses", [])
    if diagnoses:
        for dx in diagnoses[:10]:
            seq = dx.get("seq_num", "")
            badge = "🔵 " if seq == 1 else "   "
            st.caption(f"{badge}{dx.get('short_title', dx.get('icd9_code', ''))}")
    else:
        st.caption("No diagnoses on record.")

with col_med:
    st.markdown("**Medications**")
    meds = detail.get("medications", [])
    active = [m for m in meds if not m.get("enddate")]
    display_meds = active[:8] if active else meds[:8]
    if display_meds:
        for m in display_meds:
            dose = m.get("dose", "").strip() or ""
            route = m.get("route") or ""
            st.caption(f"💊 {m.get('drug', '—')} {dose} {route}".strip())
    else:
        st.caption("No medications on record.")

with col_adm:
    st.markdown("**Admissions**")
    for adm in detail.get("admissions", [])[:5]:
        admit = fmt_date(adm.get("admittime"))
        days = adm.get("duration_days")
        days_str = f" ({int(days)}d)" if days else ""
        st.caption(f"🏥 {admit}{days_str} · {adm.get('admission_type', '')}")

st.divider()

# ── Tabs: Labs / Vitals / Admissions ──────────────────────────────────────
tab_labs, tab_vitals, tab_admissions = st.tabs(["🧪 Labs", "❤️ Vitals", "🗓 Admissions"])

with tab_labs:
    try:
        labs_raw = load_labs(patient_id)
    except Exception:
        st.warning("Could not load lab data.")
        labs_raw = []

    if not labs_raw:
        st.info("No lab results found for this patient.")
    else:
        df_labs = pd.DataFrame(labs_raw)
        df_labs["charttime"] = pd.to_datetime(df_labs["charttime"], errors="coerce")
        df_labs = df_labs.dropna(subset=["charttime", "valuenum"])

        # Label selector
        available_labels = sorted(df_labs["label"].dropna().unique().tolist())
        default_labs = [lab for lab in ["Creatinine", "Hemoglobin", "White Blood Cells"]
                        if lab in available_labels]
        selected_labels = st.multiselect(
            "Select lab values to display",
            options=available_labels,
            default=default_labs or available_labels[:3],
        )

        if selected_labels:
            chart_df = (
                df_labs[df_labs["label"].isin(selected_labels)]
                .pivot_table(index="charttime", columns="label", values="valuenum", aggfunc="mean")
                .sort_index()
            )
            st.line_chart(chart_df)

            # Raw table with abnormal flagging
            st.caption("Recent values (most recent first)")
            display = (
                df_labs[df_labs["label"].isin(selected_labels)]
                .sort_values("charttime", ascending=False)
                .head(50)[["charttime", "label", "valuenum", "valueuom", "flag"]]
                .rename(columns={"charttime": "Time", "label": "Lab", "valuenum": "Value",
                                 "valueuom": "Unit", "flag": "Flag"})
            )
            display["Time"] = display["Time"].dt.strftime("%Y-%m-%d %H:%M")
            display["Flag"] = display["Flag"].fillna("")
            st.dataframe(display, use_container_width=True, hide_index=True)

with tab_vitals:
    try:
        vitals_raw = load_vitals(patient_id)
    except Exception:
        st.warning("Could not load vital signs.")
        vitals_raw = []

    if not vitals_raw:
        st.info("No vital signs found for this patient.")
    else:
        df_vitals = pd.DataFrame(vitals_raw)
        df_vitals["charttime"] = pd.to_datetime(df_vitals["charttime"], errors="coerce")
        df_vitals = df_vitals.dropna(subset=["charttime", "valuenum"])

        vital_labels = sorted(df_vitals["label"].dropna().unique().tolist())
        default_vitals = [v for v in ["Heart Rate", "Non Invasive Blood Pressure systolic"]
                          if v in vital_labels]
        selected_vitals = st.multiselect(
            "Select vital signs to display",
            options=vital_labels,
            default=default_vitals or vital_labels[:2],
        )

        if selected_vitals:
            chart_df = (
                df_vitals[df_vitals["label"].isin(selected_vitals)]
                .pivot_table(index="charttime", columns="label", values="valuenum", aggfunc="mean")
                .sort_index()
            )
            st.line_chart(chart_df)

with tab_admissions:
    admissions = detail.get("admissions", [])
    if not admissions:
        st.info("No admissions on record.")
    else:
        rows = []
        for adm in admissions:
            rows.append({
                "Admission ID": adm["hadm_id"],
                "Admitted":     fmt_datetime(adm.get("admittime")),
                "Discharged":   fmt_datetime(adm.get("dischtime")),
                "Type":         adm.get("admission_type", ""),
                "Duration (d)": round(adm["duration_days"], 1) if adm.get("duration_days") else "—",
                "Diagnosis":    adm.get("diagnosis", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
