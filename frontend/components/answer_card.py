import streamlit as st

from frontend.utils.formatting import fmt_datetime, source_type_icon


def render_answer(answer: str, citations: list[dict]) -> None:
    with st.chat_message("assistant", avatar="🏥"):
        st.markdown(answer)

    if not citations:
        return

    with st.expander(f"Sources ({len(citations)})", expanded=False):
        cols_per_row = 3
        rows = [citations[i:i + cols_per_row] for i in range(0, len(citations), cols_per_row)]
        for row in rows:
            cols = st.columns(len(row))
            for col, cit in zip(cols, row):
                with col:
                    _render_citation_card(cit)


def _render_citation_card(cit: dict) -> None:
    src  = cit["source_type"]
    icon = source_type_icon(src)
    cid  = cit["id"]
    label = cit.get("label", "")
    value = cit.get("value", "") or ""
    unit  = cit.get("unit", "") or ""
    flag  = cit.get("flag") or ""
    ts    = cit.get("timestamp")

    border_color = {
        "lab":        "#ef4444" if flag and "abnormal" in flag.lower() else "#0ea5e9",
        "medication": "#10b981",
        "vital":      "#0ea5e9",
        "diagnosis":  "#f59e0b",
        "note":       "#8b5cf6",
    }.get(src, "#0ea5e9")

    bg_color = {
        "lab":        "#fff5f5" if flag and "abnormal" in flag.lower() else "#f0f9ff",
        "medication": "#f0fdf4",
        "vital":      "#f0f9ff",
        "diagnosis":  "#fffbeb",
        "note":       "#faf5ff",
    }.get(src, "#f8fafc")

    lines = []
    if value:
        lines.append(f"**{value} {unit}".strip() + "**")
    if flag:
        lines.append(f"⚠ *{flag.upper()}*")
    if ts:
        lines.append(f"🕐 {fmt_datetime(ts)}")
    if src == "note" and cit.get("excerpt"):
        excerpt = cit["excerpt"][:100] + ("…" if len(cit["excerpt"]) > 100 else "")
        lines.append(f'*"{excerpt}"*')
        if cit.get("category"):
            lines.append(f"📄 {cit['category']}")

    body = "  \n".join(lines) if lines else ""

    st.markdown(
        f"""<div style="background:{bg_color};border:1px solid #e2e8f0;
            border-left:4px solid {border_color};border-radius:10px;
            padding:0.6rem 0.75rem;margin-bottom:0.4rem">
            <span style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.5px;color:#64748b">{icon} {cid}</span><br>
            <span style="font-weight:600;font-size:0.88rem;color:#0f172a">{label}</span>
        </div>""",
        unsafe_allow_html=True,
    )
    if body:
        with st.container():
            st.markdown(
                f"<div style='font-size:0.82rem;color:#374151;margin:-8px 0 6px 4px'>{body}</div>",
                unsafe_allow_html=True,
            )
