import base64
from pathlib import Path

import streamlit as st


def _safe(text: str) -> str:
    if text is None:
        return ""
    return str(text).replace('"', "&quot;").replace("<", "").replace(">", "")


def _image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def aplicar_estilos_globales():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #071224 0%, #08152d 100%);
        color: #e5e7eb;
    }

    .block-container {
        padding-top: 1.4rem;
        max-width: 1300px;
    }

    h1 {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.2rem;
    }

    h2 {
        font-size: 1.25rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 1.4rem;
        margin-bottom: 0.5rem;
    }

    h3 {
        font-size: 1rem;
        font-weight: 700;
        color: #e2e8f0;
    }

    p, span, label, div {
        color: #cbd5e1;
    }

    /* =========================
       SIDEBAR
    ========================= */
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #d1d5db;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: #f8fafc;
    }

    /* contenedor principal del sidebar */
    [data-testid="stSidebarContent"] {
        display: flex;
        flex-direction: column;
        padding-top: 0.6rem;
    }

    [data-testid="stSidebar"] * {
        color: #0f172a !important;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 0.2rem;
        order: 2;
    }

    [data-testid="stSidebarNav"] ul {
        padding-top: 0.25rem;
    }

    [data-testid="stSidebarNav"] li {
        margin-bottom: 0.35rem;
    }

    [data-testid="stSidebarNav"] a {
        background: #ffffff;
        border: 1px solid #d9dee7;
        border-radius: 14px;
        padding: 0.75rem 0.9rem;
        min-height: 46px;
        display: flex;
        align-items: center;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
        transition: all 0.18s ease;
        font-weight: 600;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: #f1f5f9;
        border-color: #bfd3ea;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.10);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(135deg, #cfe3ff, #e8f1ff);
        border: 1px solid #7aaef8;
        color: #0b4ea2 !important;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.16);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #0b4ea2 !important;
        font-weight: 700;
    }

    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
        font-weight: 600;
        text-transform: capitalize;
    }

    [data-testid="stSidebarNav"] a svg {
        color: inherit !important;
    }

    [data-testid="stSidebarNav"] > div:first-child {
        display: none;
    }

    /* Header custom del sidebar */
    .sidebar-brand-wrap {
        order: 0;
        margin-bottom: 0.85rem;
    }

    .sidebar-brand {
        background: #ffffff;
        border: 1px solid #d6dbe3;
        border-radius: 18px;
        padding: 0.95rem 0.9rem;
        margin: 0.15rem 0 0 0;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    }

    .sidebar-brand-inner {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    .sidebar-brand-logo {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: transparent;
        object-fit: contain;
        flex-shrink: 0;
    }

    .sidebar-brand-title {
        font-size: 1.35rem;
        line-height: 1.02;
        font-weight: 800;
        color: #143d79 !important;
        margin: 0;
    }

    .sidebar-brand-subtitle {
        font-size: 0.82rem;
        color: #64748b !important;
        margin-top: 0.18rem;
        font-weight: 600;
    }

    .sidebar-divider {
        height: 1px;
        background: #dbe2ea;
        border: none;
        margin: 0.85rem 0 0.75rem 0;
    }

    .sidebar-filters-wrap {
        order: 3;
        margin-top: 0.9rem;
    }

    .sidebar-filters-box {
        background: #ffffff;
        border: 1px solid #d6dbe3;
        border-radius: 16px;
        padding: 0.9rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    }

    .sidebar-filters-title {
        font-size: 1rem;
        font-weight: 800;
        color: #143d79 !important;
        margin-bottom: 0.65rem;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div,
    [data-testid="stSidebar"] .stNumberInput > div,
    [data-testid="stSidebar"] .stTextInput > div > div,
    [data-testid="stSidebar"] .stDateInput > div > div {
        background: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #d6dbe3 !important;
    }

    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background: #ffffff;
        border: 1px solid #d6dbe3;
        border-radius: 12px;
        padding: 0.25rem 0.5rem;
        font-weight: 700;
        color: #143d79 !important;
    }

    /* Radio mejorado dentro del bloque */
    [data-testid="stSidebar"] [role="radiogroup"] {
        background: #f8fafc;
        border: 1px solid #dbe2ea;
        border-radius: 14px;
        padding: 0.55rem 0.65rem;
        margin-bottom: 0.75rem;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 0.28rem 0.2rem;
        border-radius: 10px;
    }

    /* =========================
       CONTENIDO GENERAL
    ========================= */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #0ea5e9);
        color: white;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        transition: 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 5px 15px rgba(37,99,235,0.3);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(148,163,184,0.15);
    }

    .streamlit-expanderHeader {
        font-weight: 600;
        color: #e2e8f0;
    }

    .ui-help {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-left: 0.45rem;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        font-size: 0.72rem;
        font-weight: 800;
        color: #7dd3fc;
        background: rgba(56,189,248,0.12);
        border: 1px solid rgba(125,211,252,0.22);
        cursor: help;
        vertical-align: middle;
    }

    .ui-section-title {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        margin-bottom: 0.25rem;
    }

    .ui-divider {
        border: none;
        height: 1px;
        background: rgba(148,163,184,0.22);
        margin: 0.55rem 0 0.95rem 0;
    }

    .ui-note {
        background: rgba(30,41,59,0.7);
        padding: 0.8rem 0.95rem;
        border-left: 4px solid #38bdf8;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    .ui-hero {
        background: linear-gradient(135deg, rgba(37,99,235,0.28), rgba(14,165,233,0.18));
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        box-shadow: 0 10px 28px rgba(0,0,0,0.20);
    }

    .ui-kpi-card {
        background: rgba(9, 20, 43, 0.92);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 16px;
        padding: 1rem;
        min-height: 118px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }

    .ui-kpi-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.55rem;
    }

    .ui-kpi-title {
        font-size: 0.88rem;
        color: #93a4bf;
        font-weight: 600;
    }

    .ui-kpi-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.1;
        margin-bottom: 0.45rem;
    }

    .ui-kpi-delta {
        font-size: 0.82rem;
        font-weight: 700;
    }

    .ui-kpi-delta.pos { color: #22c55e; }
    .ui-kpi-delta.neg { color: #ef4444; }
    .ui-kpi-delta.neu { color: #cbd5e1; }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar_brand(
    title: str = "Dashboard Riesgo",
    subtitle: str = "Universidad Santo Tomás",
    logo_path: str = "assets/escudo_santo_tomas.png",
):
    logo_b64 = _image_to_base64(logo_path)

    if logo_b64:
        logo_html = f'<img class="sidebar-brand-logo" src="data:image/png;base64,{logo_b64}" alt="Escudo">'
    else:
        logo_html = '<div class="sidebar-brand-logo" style="display:flex;align-items:center;justify-content:center;font-weight:800;color:#143d79;">USTA</div>'

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand-wrap">
            <div class="sidebar-brand">
                <div class="sidebar-brand-inner">
                    {logo_html}
                    <div>
                        <div class="sidebar-brand-title">{_safe(title)}</div>
                        <div class="sidebar-brand-subtitle">{_safe(subtitle)}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_panel(
    modo_default: str = "General",
    filtros_label: str = "Parámetros Técnicos Avanzados",
    filtros_expanded: bool = False,
):
    st.sidebar.markdown(
        """
        <div class="sidebar-filters-wrap">
            <div class="sidebar-filters-box">
                <div class="sidebar-filters-title">Filtros Del Módulo</div>
        """,
        unsafe_allow_html=True,
    )

    modo = st.sidebar.radio(
        "Modo De Visualización",
        ["General", "Estadístico"],
        index=0 if modo_default == "General" else 1,
        key="sidebar_modo_visualizacion",
    )

    expander = st.sidebar.expander(filtros_label, expanded=filtros_expanded)

    st.sidebar.markdown(
        """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return modo, expander


def header_dashboard(titulo: str, subtitulo: str):
    st.markdown(f"""
    <div class="ui-hero">
        <h1>{_safe(titulo)}</h1>
        <p>{_safe(subtitulo)}</p>
    </div>
    """, unsafe_allow_html=True)


def nota(texto: str):
    st.markdown(f"""
    <div class="ui-note">{_safe(texto)}</div>
    """, unsafe_allow_html=True)


def seccion(titulo: str):
    st.markdown(f"""
    <h2>{_safe(titulo)}</h2>
    <hr class="ui-divider">
    """, unsafe_allow_html=True)


def titulo_con_ayuda(titulo: str, help_text: str, nivel: int = 3):
    tag = "h2" if nivel == 2 else "h3"
    st.markdown(f"""
    <div class="ui-section-title">
        <{tag} style="margin:0;">{_safe(titulo)}</{tag}>
        <span class="ui-help" title="{_safe(help_text)}">?</span>
    </div>
    """, unsafe_allow_html=True)


def tarjeta_kpi(titulo: str, valor: str, delta: str = "", help_text: str = ""):
    titulo_safe = _safe(titulo)
    valor_safe = _safe(valor)
    delta_safe = _safe(delta)
    help_safe = _safe(help_text)

    delta_class = "neu"
    if delta_safe.startswith("+"):
        delta_class = "pos"
    elif delta_safe.startswith("-"):
        delta_class = "neg"

    help_html = f'<span class="ui-help" title="{help_safe}">?</span>' if help_safe else ""

    st.markdown(f"""
    <div class="ui-kpi-card">
        <div class="ui-kpi-top">
            <div class="ui-kpi-title">{titulo_safe}</div>
            {help_html}
        </div>
        <div class="ui-kpi-value">{valor_safe}</div>
        <div class="ui-kpi-delta {delta_class}">{delta_safe}</div>
    </div>
    """, unsafe_allow_html=True)