import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Sidebar ─────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: #0f172a !important;
        }
        [data-testid="stSidebar"] * {
            color: #cbd5e1 !important;
        }
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stCaption {
            color: #64748b !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: #1e293b !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #cbd5e1 !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #334155 !important;
            border-color: #0ea5e9 !important;
        }

        /* ── Main layout ─────────────────────────────────── */
        .block-container {
            padding-top: 1.75rem !important;
            padding-bottom: 2rem !important;
            max-width: 1100px !important;
        }

        /* ── Page header strip ───────────────────────────── */
        .cliniq-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 1rem 1.5rem;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
            border-radius: 14px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(14, 165, 233, 0.12);
        }
        .cliniq-header h1 {
            color: #f1f5f9 !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
        }
        .cliniq-header p {
            color: #94a3b8 !important;
            font-size: 0.85rem !important;
            margin: 0 !important;
        }
        .cliniq-badge {
            margin-left: auto;
            background: #0ea5e9;
            color: white !important;
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        /* ── Metric cards ────────────────────────────────── */
        [data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem 1.25rem !important;
            transition: box-shadow 0.2s;
        }
        [data-testid="stMetric"]:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            color: #64748b !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #0f172a !important;
        }

        /* ── Stat cards (home page) ──────────────────────── */
        .stat-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            text-align: center;
        }
        .stat-card .num {
            font-size: 2rem;
            font-weight: 800;
            color: #0ea5e9;
            line-height: 1;
        }
        .stat-card .lbl {
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #94a3b8;
            margin-top: 4px;
        }

        /* ── Feature cards (home page) ───────────────────── */
        .feature-card {
            background: #ffffff;
            border: 1.5px solid #e2e8f0;
            border-radius: 16px;
            padding: 1.75rem;
            height: 100%;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .feature-card:hover {
            border-color: #0ea5e9;
            box-shadow: 0 8px 24px rgba(14, 165, 233, 0.1);
        }
        .feature-card h3 {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }
        .feature-card p {
            font-size: 0.88rem;
            color: #64748b;
            line-height: 1.6;
        }
        .feature-card ul {
            font-size: 0.85rem;
            color: #475569;
            padding-left: 1.2rem;
            margin: 0.75rem 0 0;
        }
        .feature-card ul li {
            margin-bottom: 4px;
        }

        /* ── Query type pills ────────────────────────────── */
        .qtype-pill {
            display: inline-block;
            background: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #bfdbfe;
            border-radius: 20px;
            padding: 2px 10px;
            font-size: 0.72rem;
            font-weight: 600;
            margin-right: 4px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        /* ── Citation cards ──────────────────────────────── */
        .cit-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #0ea5e9;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
        }
        .cit-card.abnormal {
            border-left-color: #ef4444;
            background: #fff5f5;
        }
        .cit-card.note {
            border-left-color: #8b5cf6;
            background: #faf5ff;
        }
        .cit-card.med {
            border-left-color: #10b981;
            background: #f0fdf4;
        }
        .cit-id {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
        }
        .cit-label {
            font-weight: 600;
            font-size: 0.9rem;
            color: #0f172a;
        }
        .cit-value {
            font-size: 0.85rem;
            color: #374151;
        }
        .cit-meta {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 2px;
        }
        .flag-abnormal {
            color: #ef4444;
            font-weight: 600;
            font-size: 0.78rem;
        }

        /* ── Chat messages ───────────────────────────────── */
        [data-testid="stChatMessage"] {
            border-radius: 12px !important;
        }

        /* ── Expanders ───────────────────────────────────── */
        [data-testid="stExpander"] {
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
        }
        [data-testid="stExpander"] summary {
            font-size: 0.85rem;
            color: #475569;
        }

        /* ── Dividers ────────────────────────────────────── */
        hr {
            border-color: #f1f5f9 !important;
            margin: 1.25rem 0 !important;
        }

        /* ── Tabs ────────────────────────────────────────── */
        [data-testid="stTabs"] [data-baseweb="tab"] {
            font-weight: 600;
            font-size: 0.85rem;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            color: #0ea5e9 !important;
        }

        /* ── Dataframe ───────────────────────────────────── */
        [data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
        }

        /* ── Alerts ──────────────────────────────────────── */
        [data-testid="stAlert"] {
            border-radius: 10px !important;
        }

        /* ── Form submit button ──────────────────────────── */
        [data-testid="stFormSubmitButton"] button {
            background: #0ea5e9 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        [data-testid="stFormSubmitButton"] button:hover {
            background: #0284c7 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str, subtitle: str, badge: str | None = None) -> None:
    badge_html = f'<span class="cliniq-badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="cliniq-header">
            <div style="font-size:1.8rem;line-height:1">{icon}</div>
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
