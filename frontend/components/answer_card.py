
import streamlit as st

from frontend.utils.formatting import flag_color, fmt_datetime, source_type_icon


def render_answer(answer: str, citations: list[dict]) -> None:
    """Render the LLM answer with inline citation badges highlighted."""
    with st.chat_message("assistant", avatar="🏥"):
        st.markdown(answer)

    if not citations:
        return

    st.divider()
    st.caption("**Sources cited in this answer**")

    cols_per_row = 3
    rows = [citations[i:i+cols_per_row] for i in range(0, len(citations), cols_per_row)]

    for row in rows:
        cols = st.columns(len(row))
        for col, cit in zip(cols, row):
            with col:
                _render_citation_badge(cit)


def _render_citation_badge(cit: dict) -> None:
    icon = source_type_icon(cit["source_type"])
    label = cit.get("label", "")
    cid = cit["id"]
    flag = cit.get("flag")
    value = cit.get("value", "")
    unit = cit.get("unit", "") or ""

    with st.expander(f"{icon} [{cid}] {label}", expanded=False):
        if cit["source_type"] == "lab":
            flag_icon = flag_color(flag)
            st.markdown(f"**Value:** {value} {unit} {flag_icon}")
            if flag:
                st.caption(f"Flag: {flag}")
            ts = cit.get("timestamp")
            if ts:
                st.caption(f"Recorded: {fmt_datetime(ts)}")

        elif cit["source_type"] == "medication":
            st.markdown(f"**Dose:** {value}")
            if unit:
                st.caption(f"Route: {unit}")
            ts = cit.get("timestamp")
            if ts:
                st.caption(f"Started: {fmt_datetime(ts)}")

        elif cit["source_type"] == "vital":
            st.markdown(f"**Value:** {value} {unit}")
            ts = cit.get("timestamp")
            if ts:
                st.caption(f"Recorded: {fmt_datetime(ts)}")

        elif cit["source_type"] == "diagnosis":
            st.markdown(f"{value or label}")

        elif cit["source_type"] == "note":
            excerpt = cit.get("excerpt")
            if excerpt:
                st.markdown(f"> {excerpt}")
            st.caption(f"Category: {cit.get('category', '')}")
