from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def _safe(text: str) -> str:
    if text is None:
        return ""
    return str(text)


def _image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def _theme_tokens(modo: str = "General") -> dict:
    if modo == "Estadístico":
        return {
            "APP_BG_START": "#FFFFFF",
            "APP_BG_END": "#FFF8FA",
            "TEXT_MAIN": "#0F172A",
            "TEXT_SOFT": "#334155",
            "TEXT_MUTED": "#64748B",
            "TEXT_INVERSE": "#F8FAFC",
            "ACCENT_MAIN": "#9F1239",
            "ACCENT_SECOND": "#BE123C",
            "ACCENT_SOFT": "rgba(190, 24, 93, 0.10)",
            "ACCENT_BORDER": "rgba(190, 24, 93, 0.22)",
            "CARD_BG": "#FFFFFF",
            "PANEL_BG": "#FFFFFF",
            "PANEL_BG_2": "#FFF7F9",
            "SIDEBAR_BG": "#7A1633",
            "SIDEBAR_BG_2": "#5E1027",
            "SIDEBAR_TEXT": "#FDF2F8",
            "SIDEBAR_BORDER": "rgba(255, 255, 255, 0.10)",
            "SUCCESS": "#16A34A",
            "DANGER": "#DC2626",
            "WARNING": "#D97706",
            "PLOT_GRID": "rgba(148, 163, 184, 0.18)",
            "BORDER_SOFT": "rgba(148, 163, 184, 0.20)",
            "SHADOW": "0 10px 28px rgba(15, 23, 42, 0.08)",
            "ACTIVE_NAV_TEXT": "#7A1633",
        }

    return {
        "APP_BG_START": "#FFFFFF",
        "APP_BG_END": "#F8FBFF",
        "TEXT_MAIN": "#0F172A",
        "TEXT_SOFT": "#334155",
        "TEXT_MUTED": "#64748B",
        "TEXT_INVERSE": "#F8FAFC",
        "ACCENT_MAIN": "#1D4ED8",
        "ACCENT_SECOND": "#2563EB",
        "ACCENT_SOFT": "rgba(37, 99, 235, 0.10)",
        "ACCENT_BORDER": "rgba(37, 99, 235, 0.20)",
        "CARD_BG": "#FFFFFF",
        "PANEL_BG": "#FFFFFF",
        "PANEL_BG_2": "#F8FBFF",
        "SIDEBAR_BG": "#0B3A8C",
        "SIDEBAR_BG_2": "#082C6C",
        "SIDEBAR_TEXT": "#EFF6FF",
        "SIDEBAR_BORDER": "rgba(255, 255, 255, 0.10)",
        "SUCCESS": "#16A34A",
        "DANGER": "#DC2626",
        "WARNING": "#D97706",
        "PLOT_GRID": "rgba(148, 163, 184, 0.18)",
        "BORDER_SOFT": "rgba(148, 163, 184, 0.20)",
        "SHADOW": "0 10px 28px rgba(15, 23, 42, 0.08)",
        "ACTIVE_NAV_TEXT": "#1D4ED8",
    }


def aplicar_estilos_globales(modo: str = "General"):
    theme = _theme_tokens(modo)

    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');

    :root {
        --app-bg-start: __APP_BG_START__;
        --app-bg-end: __APP_BG_END__;
        --text-main: __TEXT_MAIN__;
        --text-soft: __TEXT_SOFT__;
        --text-muted: __TEXT_MUTED__;
        --text-inverse: __TEXT_INVERSE__;
        --accent-main: __ACCENT_MAIN__;
        --accent-second: __ACCENT_SECOND__;
        --accent-soft: __ACCENT_SOFT__;
        --accent-border: __ACCENT_BORDER__;
        --card-bg: __CARD_BG__;
        --panel-bg: __PANEL_BG__;
        --panel-bg-2: __PANEL_BG_2__;
        --sidebar-bg: __SIDEBAR_BG__;
        --sidebar-bg-2: __SIDEBAR_BG_2__;
        --sidebar-text: __SIDEBAR_TEXT__;
        --sidebar-border: __SIDEBAR_BORDER__;
        --success: __SUCCESS__;
        --danger: __DANGER__;
        --warning: __WARNING__;
        --plot-grid: __PLOT_GRID__;
        --border-soft: __BORDER_SOFT__;
        --shadow-main: __SHADOW__;
        --active-nav-text: __ACTIVE_NAV_TEXT__;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top right, var(--accent-soft), transparent 24%),
            linear-gradient(180deg, var(--app-bg-start) 0%, var(--app-bg-end) 100%);
        color: var(--text-soft);
    }

    .block-container {
        padding-top: 1.30rem;
        max-width: 1320px;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--text-main) !important;
    }

    h1 {
        font-size: 2.15rem;
        font-weight: 800;
        margin-bottom: 0.20rem;
    }

    h2 {
        font-size: 1.18rem;
        font-weight: 800;
        margin-top: 1.35rem;
        margin-bottom: 0.40rem;
    }

    h3 {
        font-size: 1rem;
        font-weight: 700;
    }

    .stMarkdown, .stMarkdown p, .stMarkdown li, .stText, p, label {
        color: var(--text-soft) !important;
    }

    div[data-testid="stAppViewContainer"] .element-container,
    div[data-testid="stAppViewContainer"] .stMarkdown,
    div[data-testid="stAppViewContainer"] .stCaption,
    div[data-testid="stAppViewContainer"] p,
    div[data-testid="stAppViewContainer"] li {
        color: var(--text-soft);
    }

    /* =========================
       SIDEBAR
    ========================= */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-2) 100%);
        border-right: 1px solid var(--sidebar-border);
    }

    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-2) 100%);
    }

    [data-testid="stSidebarContent"] {
        display: flex;
        flex-direction: column;
        padding-top: 0.6rem;
    }

    [data-testid="stSidebar"] * {
        color: var(--sidebar-text) !important;
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
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 16px;
        padding: 0.80rem 0.95rem;
        min-height: 48px;
        display: flex;
        align-items: center;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.10);
        transition: all 0.18s ease;
        font-weight: 700;
        backdrop-filter: blur(4px);
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.16);
        border-color: rgba(255, 255, 255, 0.24);
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.14);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.85);
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.14);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] span,
    [data-testid="stSidebarNav"] a[aria-current="page"] p,
    [data-testid="stSidebarNav"] a[aria-current="page"] div {
        color: var(--active-nav-text) !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
        font-weight: 700;
        text-transform: capitalize;
        opacity: 1 !important;
    }

    [data-testid="stSidebarNav"] a svg {
        color: inherit !important;
    }

    [data-testid="stSidebarNav"] > div:first-child {
        display: none;
    }

    .sidebar-brand-wrap {
        order: 0;
        margin-bottom: 0.85rem;
    }

    .sidebar-brand {
        background: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.70);
        border-radius: 20px;
        padding: 0.95rem 0.9rem;
        margin: 0.15rem 0 0 0;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
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
        color: var(--accent-main) !important;
        margin: 0;
    }

    .sidebar-brand-subtitle {
        font-size: 0.82rem;
        color: #64748b !important;
        margin-top: 0.18rem;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .streamlit-expander {
        margin-top: 0.1rem;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.70) !important;
        border-radius: 20px !important;
        padding: 0.85rem 0.95rem !important;
        font-weight: 800 !important;
        color: var(--accent-main) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    }

    [data-testid="stSidebar"] details[open] summary {
        border-bottom-left-radius: 0 !important;
        border-bottom-right-radius: 0 !important;
        background: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.70) !important;
    }

    [data-testid="stSidebar"] details > div {
        background: rgba(255, 255, 255, 0.98);
        border: 1px solid rgba(255, 255, 255, 0.70);
        border-top: none;
        border-bottom-left-radius: 20px;
        border-bottom-right-radius: 20px;
        padding: 0.95rem 0.9rem 0.85rem 0.9rem !important;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.12);
        margin-top: -2px;
        color: #0F172A !important;
    }

    [data-testid="stSidebar"] details > div * {
        opacity: 1 !important;
    }

    .sidebar-panel-label {
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--accent-main) !important;
        margin: 0.15rem 0 0.45rem 0;
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        background: #f8fafc;
        border: 1px solid #dbe2ea;
        border-radius: 16px;
        padding: 0.8rem 0.8rem;
        margin-bottom: 0.9rem;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.85);
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding: 0.40rem 0.45rem !important;
        border-radius: 10px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label,
    [data-testid="stSidebar"] [role="radiogroup"] span,
    [data-testid="stSidebar"] [role="radiogroup"] div,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stCheckbox span,
    [data-testid="stSidebar"] .stCheckbox div,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stSlider span,
    [data-testid="stSidebar"] .stSlider div {
        color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] details summary,
    [data-testid="stSidebar"] details summary * {
        color: var(--accent-main) !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.20rem !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        background: transparent !important;
        border-radius: 10px !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stRadio label p,
    [data-testid="stSidebar"] .stRadio label span,
    [data-testid="stSidebar"] .stRadio label div {
        color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] .stRadio label[data-checked="true"] {
        background: color-mix(in srgb, var(--accent-main) 12%, white) !important;
        border-radius: 10px !important;
        padding-left: 0.35rem !important;
        padding-right: 0.35rem !important;
    }

    [data-testid="stSidebar"] .stRadio label[data-checked="true"] p,
    [data-testid="stSidebar"] .stRadio label[data-checked="true"] span,
    [data-testid="stSidebar"] .stRadio label[data-checked="true"] div {
        color: var(--accent-main) !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stCheckbox,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stMultiSelect,
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stDateInput,
    [data-testid="stSidebar"] .stNumberInput {
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stCheckbox p,
    [data-testid="stSidebar"] .stCheckbox span,
    [data-testid="stSidebar"] .stCheckbox div {
        color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div,
    [data-testid="stSidebar"] .stTextInput > div > div,
    [data-testid="stSidebar"] .stDateInput > div > div {
        background: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #d6dbe3 !important;
    }

    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] *,
    [data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] *,
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stDateInput input {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] * {
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stSlider [role="slider"] {
        background: var(--accent-main) !important;
        border-color: var(--accent-main) !important;
    }

    [data-testid="stSidebar"] .stSlider div[data-testid="stTickBar"] {
        background: rgba(148, 163, 184, 0.35) !important;
    }

    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] + div,
    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] ~ div {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] .stNumberInput > div {
        background: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #d6dbe3 !important;
        overflow: hidden !important;
    }

    [data-testid="stSidebar"] .stNumberInput input {
        background: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        caret-color: #0f172a !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stNumberInput button {
        background: #ffffff !important;
        color: var(--accent-main) !important;
        border: none !important;
        opacity: 1 !important;
    }

    /* =========================
       CONTENIDO GENERAL
    ========================= */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-main), var(--accent-second));
        color: white;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 700;
        border: none;
        transition: 0.2s;
        box-shadow: 0 6px 16px color-mix(in srgb, var(--accent-main) 18%, transparent);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--border-soft);
        background: #ffffff;
        box-shadow: var(--shadow-main);
    }

    div[data-testid="stPlotlyChart"] {
        border-radius: 20px;
        overflow: hidden;
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid var(--border-soft);
        padding: 0.55rem 0.45rem 0.15rem 0.45rem;
        box-shadow: var(--shadow-main);
        margin-bottom: 0.55rem;
    }

    .ui-help {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-left: 0.45rem;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        font-size: 0.72rem;
        font-weight: 800;
        color: var(--accent-main);
        background: var(--accent-soft);
        border: 1px solid var(--accent-border);
        cursor: help;
        vertical-align: middle;
        flex-shrink: 0;
    }

    .ui-section-title {
        display: flex;
        align-items: center;
        gap: 0.30rem;
        margin-bottom: 0.25rem;
    }

    .ui-divider {
        border: none;
        height: 1px;
        background: rgba(148, 163, 184, 0.22);
        margin: 0.55rem 0 0.95rem 0;
    }

    .ui-note {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        padding: 0.95rem 1rem;
        border-left: 4px solid var(--accent-main);
        border-radius: 16px;
        margin-bottom: 1rem;
        border: 1px solid var(--border-soft);
        box-shadow: var(--shadow-main);
        color: var(--text-soft) !important;
    }

    .ui-note * {
        color: var(--text-soft) !important;
    }

    .ui-hero {
        background: linear-gradient(
            135deg,
            color-mix(in srgb, var(--accent-main) 10%, white),
            color-mix(in srgb, var(--accent-second) 6%, white)
        );
        padding: 1.55rem;
        border-radius: 20px;
        margin-bottom: 0.95rem;
        border: 1px solid var(--accent-border);
        box-shadow: var(--shadow-main);
    }

    .ui-hero h1,
    .ui-hero h2,
    .ui-hero h3,
    .ui-hero p,
    .ui-hero span,
    .ui-hero div {
        color: var(--text-main) !important;
    }

    .ui-hero-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        flex-wrap: wrap;
        margin-bottom: 0.25rem;
    }

    .ui-mode-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.35rem;
        min-height: 34px;
        padding: 0.42rem 0.92rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 900;
        letter-spacing: 0.02em;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background: linear-gradient(135deg, var(--accent-main), var(--accent-second));
        border: 1px solid color-mix(in srgb, var(--accent-main) 40%, white);
        box-shadow: 0 8px 18px color-mix(in srgb, var(--accent-main) 24%, transparent);
        white-space: nowrap;
        opacity: 1 !important;
    }

    .ui-mode-badge,
    .ui-mode-badge span,
    .ui-mode-badge div,
    .ui-mode-badge p,
    .ui-plot-head .ui-mode-badge,
    .ui-plot-head .ui-mode-badge span,
    .ui-plot-head .ui-mode-badge div,
    .ui-plot-head .ui-mode-badge p,
    .ui-hero .ui-mode-badge,
    .ui-hero .ui-mode-badge span,
    .ui-hero .ui-mode-badge div,
    .ui-hero .ui-mode-badge p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        opacity: 1 !important;
        font-weight: 900 !important;
    }

    .ui-kpi-card {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: 18px;
        padding: 0.95rem 1rem 0.95rem 1rem;
        min-height: 124px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        transition: all 0.18s ease;
        position: relative;
        overflow: hidden;
    }

    .ui-kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-main), var(--accent-second));
    }

    .ui-kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 28px rgba(15, 23, 42, 0.10);
        border-color: color-mix(in srgb, var(--accent-main) 22%, #cbd5e1);
    }

    .ui-kpi-card * {
        opacity: 1 !important;
    }

    .ui-kpi-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.5rem;
        margin-bottom: 0.65rem;
    }

    .ui-kpi-title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 900;
        color: var(--text-muted) !important;
        line-height: 1.2;
    }

    .ui-kpi-value {
        font-size: 1.9rem;
        font-weight: 900;
        color: var(--text-main) !important;
        line-height: 1.05;
        margin-bottom: 0.28rem;
        letter-spacing: -0.02em;
    }

    .ui-kpi-delta {
        font-size: 0.84rem;
        font-weight: 800;
        line-height: 1.3;
        margin-bottom: 0.22rem;
    }

    .ui-kpi-delta.pos { color: var(--success) !important; }
    .ui-kpi-delta.neg { color: var(--danger) !important; }
    .ui-kpi-delta.neu { color: var(--text-soft) !important; }

    .ui-kpi-sub {
        font-size: 0.88rem;
        color: var(--text-soft) !important;
        line-height: 1.45;
        margin-top: 0.12rem;
    }

    .ui-plot-head {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1rem 1rem 0.9rem 1rem;
        margin-bottom: 0.65rem;
        box-shadow: var(--shadow-main);
    }

    .ui-plot-head * {
        color: var(--text-soft) !important;
    }

    .ui-plot-head-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        flex-wrap: wrap;
    }

    .ui-plot-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: var(--text-main) !important;
        margin: 0;
    }

    .ui-plot-caption {
        margin-top: 0.42rem;
        font-size: 0.92rem;
        color: var(--text-soft) !important;
        line-height: 1.45;
    }

    .ui-plot-foot {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid var(--border-soft);
        border-radius: 16px;
        padding: 0.78rem 0.95rem;
        margin-top: 0.1rem;
        margin-bottom: 1rem;
        color: var(--text-soft) !important;
        box-shadow: var(--shadow-main);
    }

    .ui-toolbar-wrap {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 1rem 1rem 0.55rem 1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
    }

    .ui-toolbar-title {
        font-size: 0.80rem;
        font-weight: 900;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.75rem;
    }

    .ui-toolbar-wrap [data-testid="stHorizontalBlock"] {
        gap: 0.75rem;
        align-items: stretch;
    }

    .ui-toolbar-wrap .stCheckbox {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #dbe4ee;
        border-radius: 14px;
        padding: 0.5rem 0.8rem;
        min-height: 48px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        transition: all 0.18s ease;
    }

    .ui-toolbar-wrap .stCheckbox:hover {
        border-color: color-mix(in srgb, var(--accent-main) 30%, #cbd5e1);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
        transform: translateY(-1px);
    }

    .ui-toolbar-wrap .stCheckbox label,
    .ui-toolbar-wrap .stCheckbox span,
    .ui-toolbar-wrap .stCheckbox div {
        color: var(--text-main) !important;
        font-weight: 700 !important;
    }

    .ui-toolbar-wrap input[type="checkbox"] {
        accent-color: var(--accent-main);
    }

    .ui-toolbar-label {
        font-size: 0.82rem;
        font-weight: 800;
        color: var(--text-muted) !important;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* =========================
       TABS
    ========================= */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.55rem;
        background: linear-gradient(180deg, #eef4fb 0%, #e8f0fa 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        padding: 0.4rem;
        border-radius: 18px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        width: fit-content;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 44px;
        padding: 0.55rem 1rem !important;
        border-radius: 12px !important;
        background: transparent !important;
        color: var(--text-soft) !important;
        font-weight: 700 !important;
        border: 1px solid transparent !important;
        transition: all 0.18s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.72) !important;
        color: var(--text-main) !important;
        border-color: rgba(148, 163, 184, 0.18) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
        color: var(--accent-main) !important;
        border: 1px solid color-mix(in srgb, var(--accent-main) 20%, #cbd5e1) !important;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
    }

    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] div {
        color: var(--accent-main) !important;
        font-weight: 800 !important;
    }

    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {
        color: inherit !important;
    }

    /* FIX DE LEGIBILIDAD EN FILTROS DEL SIDEBAR */
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stCheckbox p,
    [data-testid="stSidebar"] .stCheckbox span,
    [data-testid="stSidebar"] .stCheckbox div,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stSlider span,
    [data-testid="stSidebar"] .stSlider div,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] label[data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] div[data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] p[data-testid="stWidgetLabel"] {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    </style>
    """

    for key, value in theme.items():
        css = css.replace(f"__{key}__", value)

    st.markdown(css, unsafe_allow_html=True)


def render_sidebar_brand(
    title: str = "Dashboard Riesgo",
    subtitle: str = "Universidad Santo Tomás",
    logo_path: str = "assets/escudo_santo_tomas.png",
):
    logo_b64 = _image_to_base64(logo_path)

    if logo_b64:
        logo_html = f'<img class="sidebar-brand-logo" src="data:image/png;base64,{logo_b64}" alt="Escudo">'
    else:
        logo_html = '<div class="sidebar-brand-logo" style="display:flex;align-items:center;justify-content:center;font-weight:800;color:var(--accent-main);">USTA</div>'

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
    filtros_label: str = "Opciones Del Módulo",
    filtros_expanded: bool = False,
):
    expander = st.sidebar.expander("Filtros Del Módulo", expanded=True)

    with expander:
        st.markdown('<div class="sidebar-panel-label">Modo De Visualización</div>', unsafe_allow_html=True)

        modo = st.radio(
            "Modo De Visualización",
            ["General", "Estadístico"],
            index=0 if modo_default == "General" else 1,
            key="sidebar_modo_visualizacion",
            label_visibility="collapsed",
        )

        inner_expander = st.expander(filtros_label, expanded=filtros_expanded)

    return modo, inner_expander


def mode_badge(modo: str):
    st.markdown(
        f'<span class="ui-mode-badge">Modo {_safe(modo)}</span>',
        unsafe_allow_html=True,
    )


def header_dashboard(titulo: str, subtitulo: str, modo: str | None = None):
    badge_html = f'<span class="ui-mode-badge">Modo {_safe(modo)}</span>' if modo else ""

    st.markdown(
        f"""
        <div class="ui-hero">
            <div class="ui-hero-top">
                <h1 style="margin:0;">{_safe(titulo)}</h1>
                {badge_html}
            </div>
            <p style="margin:0.15rem 0 0 0;">{_safe(subtitulo)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nota(texto: str):
    st.markdown(
        f"""
        <div class="ui-note">{_safe(texto)}</div>
        """,
        unsafe_allow_html=True,
    )


def seccion(titulo: str):
    st.markdown(
        f"""
        <h2>{_safe(titulo)}</h2>
        <hr class="ui-divider">
        """,
        unsafe_allow_html=True,
    )


def titulo_con_ayuda(titulo: str, help_text: str, nivel: int = 3):
    tag = "h2" if nivel == 2 else "h3"
    st.markdown(
        f"""
        <div class="ui-section-title">
            <{tag} style="margin:0;">{_safe(titulo)}</{tag}>
            <span class="ui-help" title="{_safe(help_text)}">?</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_kpi(
    titulo: str,
    valor: str,
    delta: str = "",
    help_text: str = "",
    subtexto: str = "",
):
    titulo_safe = _safe(titulo)
    valor_safe = _safe(valor)
    delta_safe = _safe(delta)
    help_safe = _safe(help_text)
    subtexto_safe = _safe(subtexto)

    delta_class = "neu"
    if delta_safe.startswith("+"):
        delta_class = "pos"
    elif delta_safe.startswith("-"):
        delta_class = "neg"

    help_html = f'<span class="ui-help" title="{help_safe}">?</span>' if help_safe else ""
    delta_html = f'<div class="ui-kpi-delta {delta_class}">{delta_safe}</div>' if delta_safe else ""
    subtexto_html = f'<div class="ui-kpi-sub">{subtexto_safe}</div>' if subtexto_safe else ""

    html = (
        f'<div class="ui-kpi-card">'
        f'<div class="ui-kpi-top">'
        f'<div class="ui-kpi-title">{titulo_safe}</div>'
        f'{help_html}'
        f'</div>'
        f'<div class="ui-kpi-value">{valor_safe}</div>'
        f'{delta_html}'
        f'{subtexto_html}'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def plot_card_header(titulo: str, help_text: str, modo: str = "General", caption: str = ""):
    caption_html = f'<div class="ui-plot-caption">{_safe(caption)}</div>' if caption else ""

    st.markdown(
        f"""
        <div class="ui-plot-head">
            <div class="ui-plot-head-top">
                <div class="ui-section-title" style="margin:0;">
                    <div class="ui-plot-title">{_safe(titulo)}</div>
                    <span class="ui-help" title="{_safe(help_text)}">?</span>
                </div>
                <span class="ui-mode-badge">Modo {_safe(modo)}</span>
            </div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot_card_footer(texto: str):
    st.markdown(
        f"""
        <div class="ui-plot-foot">{_safe(texto)}</div>
        """,
        unsafe_allow_html=True,
    )


def toolbar_label(texto: str):
    st.markdown(f'<div class="ui-toolbar-label">{_safe(texto)}</div>', unsafe_allow_html=True)


def toolbar_open(title: str = "Capas Del Gráfico"):
    st.markdown(
        f"""
        <div class="ui-toolbar-wrap">
            <div class="ui-toolbar-title">{_safe(title)}</div>
        """,
        unsafe_allow_html=True,
    )


def toolbar_close():
    st.markdown("</div>", unsafe_allow_html=True)