import streamlit as st

from frontend.utils.formatting import fmt_datetime, source_type_icon


def render_answer(answer: str, citations: list[dict]) -> None:
    with st.chat_message("assistant", avatar="🏥"):
        st.markdown(answer)

    if not citations:
        return

    st.markdown(
        "<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;color:#64748b;margin:1rem 0 0.5rem'>Sources</div>",
        unsafe_allow_html=True,
    )

    cols_per_row = 3
    rows = [citations[i:i + cols_per_row] for i in range(0, len(citations), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, cit in zip(cols, row):
            with col:
                _render_citation_card(cit)


def _render_citation_card(cit: dict) -> None:
    src = cit["source_type"]
    icon = source_type_icon(src)
    cid = cit["id"]
    label = cit.get("label", "")
    value = cit.get("value", "") or ""
    unit = cit.get("unit", "") or ""
    flag = cit.get("flag") or ""
    ts = cit.get("timestamp")

    card_class = "cit-card"
    if flag and "abnormal" in flag.lower():
        card_class += " abnormal"
    elif src == "note":
        card_class += " note"
    elif src == "medication":
        card_class += " med"

    flag_html = ""
    if flag:
        flag_html = f'<div class="flag-abnormal">⚠ {flag.upper()}</div>'

    ts_html = ""
    if ts:
        ts_html = f'<div class="cit-meta">🕐 {fmt_datetime(ts)}</div>'

    value_html = ""
    if value:
        value_str = f"{value} {unit}".strip()
        value_html = f'<div class="cit-value">{value_str}</div>'

    excerpt_html = ""
    if src == "note" and cit.get("excerpt"):
        excerpt = cit["excerpt"][:120] + ("…" if len(cit["excerpt"]) > 120 else "")
        excerpt_html = f'<div class="cit-value" style="font-style:italic">"{excerpt}"</div>'
        category = cit.get("category", "")
        if category:
            ts_html = f'<div class="cit-meta">📄 {category}</div>'

    st.markdown(
        f"""
        <div class="{card_class}">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span class="cit-id">{icon} {cid}</span>
                {flag_html}
            </div>
            <div class="cit-label">{label}</div>
            {value_html}
            {excerpt_html}
            {ts_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
