import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

from frontend.components.patient_selector import render_patient_selector
from frontend.utils import api_client
from frontend.utils.formatting import fmt_date, fmt_datetime
from frontend.utils.styles import inject_css, page_header

st.set_page_config(page_title="Patient Explorer · ClinIQ", page_icon="🔍", layout="wide")
inject_css()

patient_id = render_patient_selector(key="explorer_patient_id")

page_header("🔍", "Patient Explorer", "Browse structured records, labs, and vitals")

if patient_id is None:
    st.info("Select a patient from the sidebar.")
    st.stop()


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

# ── Patient header ─────────────────────────────────────────────────────────
alive = detail.get("alive", True)
status_color = "#10b981" if alive else "#94a3b8"
status_label = "Alive" if alive else "Deceased"

st.markdown(
    f"""
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;
                padding:1.25rem 1.5rem;margin-bottom:1.25rem;
                display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap">
        <div>
            <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.5px;color:#94a3b8">Patient ID</div>
            <div style="font-size:1.8rem;font-weight:800;color:#0f172a;line-height:1.1">
                #{detail['subject_id']}
            </div>
        </div>
        <div style="height:40px;width:1px;background:#e2e8f0"></div>
        <div>
            <div style="font-size:0.7rem;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.5px;color:#94a3b8">Gender</div>
            <div style="font-size:1.1rem;font-weight:700;color:#374151">
                {detail.get('gender') or '—'}
            </div>
        </div>
        <div>
            <div style="font-size:0.7rem;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.5px;color:#94a3b8">Age</div>
            <div style="font-size:1.1rem;font-weight:700;color:#374151">
                {detail.get('age') or '—'}
            </div>
        </div>
        <div>
            <div style="font-size:0.7rem;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.5px;color:#94a3b8">Admissions</div>
            <div style="font-size:1.1rem;font-weight:700;color:#374151">
                {len(detail.get('admissions', []))}
            </div>
        </div>
        <div style="margin-left:auto;display:flex;align-items:center;gap:6px">
            <div style="width:8px;height:8px;border-radius:50%;background:{status_color};
                        box-shadow:0 0 8px {status_color}80"></div>
            <span style="font-size:0.85rem;font-weight:600;color:{status_color}">
                {status_label}
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Overview columns ───────────────────────────────────────────────────────
col_dx, col_med, col_adm = st.columns(3)

with col_dx:
    st.markdown(
        "<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;color:#64748b;margin-bottom:8px'>Diagnoses</div>",
        unsafe_allow_html=True,
    )
    diagnoses = detail.get("diagnoses", [])
    if diagnoses:
        for dx in diagnoses[:8]:
            is_primary = dx.get("seq_num") == 1
            dot_color = "#0ea5e9" if is_primary else "#e2e8f0"
            title = dx.get("short_title") or dx.get("icd9_code") or "—"
            st.markdown(
                f"""
                <div style="display:flex;align-items:flex-start;gap:8px;
                            padding:5px 0;border-bottom:1px solid #f1f5f9">
                    <div style="width:7px;height:7px;border-radius:50%;
                                background:{dot_color};margin-top:5px;flex-shrink:0"></div>
                    <span style="font-size:0.82rem;color:#374151;line-height:1.4">{title}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("No diagnoses on record.")

with col_med:
    st.markdown(
        "<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;color:#64748b;margin-bottom:8px'>Medications</div>",
        unsafe_allow_html=True,
    )
    meds = detail.get("medications", [])
    active = [m for m in meds if not m.get("enddate")] or meds
    for m in active[:8]:
        dose = (m.get("dose") or "").strip()
        route = m.get("route") or ""
        sub = f"{dose} {route}".strip()
        st.markdown(
            f"""
            <div style="display:flex;align-items:flex-start;gap:8px;
                        padding:5px 0;border-bottom:1px solid #f1f5f9">
                <div style="width:7px;height:7px;border-radius:50%;
                            background:#10b981;margin-top:5px;flex-shrink:0"></div>
                <div>
                    <div style="font-size:0.82rem;color:#374151;font-weight:600">
                        {m.get('drug','—')}
                    </div>
                    {f'<div style="font-size:0.72rem;color:#94a3b8">{sub}</div>' if sub else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if not active:
        st.caption("No medications on record.")

with col_adm:
    st.markdown(
        "<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;color:#64748b;margin-bottom:8px'>Admissions</div>",
        unsafe_allow_html=True,
    )
    for adm in detail.get("admissions", [])[:5]:
        admit = fmt_date(adm.get("admittime"))
        days = adm.get("duration_days")
        days_str = f"{int(days)}d" if days else "—"
        adm_type = adm.get("admission_type") or ""
        st.markdown(
            f"""
            <div style="padding:6px 0;border-bottom:1px solid #f1f5f9">
                <div style="font-size:0.82rem;font-weight:600;color:#374151">{admit}</div>
                <div style="display:flex;gap:6px;margin-top:2px">
                    <span style="font-size:0.7rem;color:#94a3b8">{adm_type}</span>
                    <span style="font-size:0.7rem;font-weight:600;color:#0ea5e9">{days_str}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────
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
        df = pd.DataFrame(labs_raw)
        df["charttime"] = pd.to_datetime(df["charttime"], errors="coerce")
        df = df.dropna(subset=["charttime", "valuenum"])

        available = sorted(df["label"].dropna().unique().tolist())
        default = [l for l in ["Creatinine", "Hemoglobin", "White Blood Cells"] if l in available]
        selected = st.multiselect("Select labs to chart", available, default=default or available[:3])

        if selected:
            chart_df = (
                df[df["label"].isin(selected)]
                .pivot_table(index="charttime", columns="label", values="valuenum", aggfunc="mean")
                .sort_index()
            )
            st.line_chart(chart_df, height=280)

            st.markdown(
                "<div style='font-size:0.75rem;font-weight:600;text-transform:uppercase;"
                "letter-spacing:0.5px;color:#64748b;margin:1rem 0 0.5rem'>Recent Values</div>",
                unsafe_allow_html=True,
            )
            display = (
                df[df["label"].isin(selected)]
                .sort_values("charttime", ascending=False)
                .head(50)[["charttime", "label", "valuenum", "valueuom", "flag"]]
                .rename(columns={
                    "charttime": "Time", "label": "Lab",
                    "valuenum": "Value", "valueuom": "Unit", "flag": "Flag",
                })
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
        df_v = pd.DataFrame(vitals_raw)
        df_v["charttime"] = pd.to_datetime(df_v["charttime"], errors="coerce")
        df_v = df_v.dropna(subset=["charttime", "valuenum"])

        vital_labels = sorted(df_v["label"].dropna().unique().tolist())
        default_v = [v for v in ["Heart Rate", "Non Invasive Blood Pressure systolic"] if v in vital_labels]
        selected_v = st.multiselect("Select vitals", vital_labels, default=default_v or vital_labels[:2])

        if selected_v:
            chart_df_v = (
                df_v[df_v["label"].isin(selected_v)]
                .pivot_table(index="charttime", columns="label", values="valuenum", aggfunc="mean")
                .sort_index()
            )
            st.line_chart(chart_df_v, height=280)

with tab_admissions:
    admissions = detail.get("admissions", [])
    if not admissions:
        st.info("No admissions on record.")
    else:
        rows = [{
            "Admission ID":   adm["hadm_id"],
            "Admitted":       fmt_datetime(adm.get("admittime")),
            "Discharged":     fmt_datetime(adm.get("dischtime")),
            "Type":           adm.get("admission_type", ""),
            "Duration (days)": round(adm["duration_days"], 1) if adm.get("duration_days") else "—",
            "Diagnosis":      adm.get("diagnosis", ""),
        } for adm in admissions]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
