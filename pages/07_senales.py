import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import (
    header_dashboard,
    seccion,
    nota,
    tarjeta_kpi,
    plot_card_footer,
)

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import download_single_ticker
from src.indicators import compute_all_indicators
from src.signals import evaluate_signals

ensure_project_dirs()

SIGNAL_LABELS = {
    "macd_buy": "MACD compra",
    "macd_sell": "MACD venta",
    "rsi_buy": "RSI sobreventa",
    "rsi_sell": "RSI sobrecompra",
    "boll_buy": "Bollinger compra",
    "boll_sell": "Bollinger venta",
    "golden_cross": "Golden cross",
    "death_cross": "Death cross",
    "stoch_buy": "Estocástico compra",
    "stoch_sell": "Estocástico venta",
}


# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros De Señales",
    filtros_expanded=False,
)


# ==============================
# SIDEBAR
# ==============================
with filtros_sidebar:
    horizonte = st.selectbox(
        "Horizonte de análisis",
        [
            "1 mes",
            "Trimestre",
            "Semestre",
            "1 año",
            "3 años",
            "5 años",
            "Personalizado",
        ],
        index=3,
        key="sig_horizonte",
    )

    fecha_fin_ref = pd.to_datetime(DEFAULT_END_DATE)

    if horizonte == "1 mes":
        start_date = (fecha_fin_ref - pd.DateOffset(months=1)).date()
        end_date = fecha_fin_ref.date()
    elif horizonte == "Trimestre":
        start_date = (fecha_fin_ref - pd.DateOffset(months=3)).date()
        end_date = fecha_fin_ref.date()
    elif horizonte == "Semestre":
        start_date = (fecha_fin_ref - pd.DateOffset(months=6)).date()
        end_date = fecha_fin_ref.date()
    elif horizonte == "1 año":
        start_date = (fecha_fin_ref - pd.DateOffset(years=1)).date()
        end_date = fecha_fin_ref.date()
    elif horizonte == "3 años":
        start_date = (fecha_fin_ref - pd.DateOffset(years=3)).date()
        end_date = fecha_fin_ref.date()
    elif horizonte == "5 años":
        start_date = (fecha_fin_ref - pd.DateOffset(years=5)).date()
        end_date = fecha_fin_ref.date()
    else:
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="sig_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="sig_end")

    mostrar_detalle = st.checkbox("Mostrar detalle por activo", value=False, key="sig_detalle")

    with st.expander("Filtros secundarios", expanded=False):
        rsi_overbought = st.slider(
            "RSI sobrecompra",
            min_value=60,
            max_value=90,
            value=70,
            key="sig_rsi_ob",
        )
        rsi_oversold = st.slider(
            "RSI sobreventa",
            min_value=10,
            max_value=40,
            value=30,
            key="sig_rsi_os",
        )
        stoch_overbought = st.slider(
            "Estocástico sobrecompra",
            min_value=60,
            max_value=95,
            value=80,
            key="sig_stoch_ob",
        )
        stoch_oversold = st.slider(
            "Estocástico sobreventa",
            min_value=5,
            max_value=40,
            value=20,
            key="sig_stoch_os",
        )


# ==============================
# ESTILOS LOCALES
# ==============================
st.markdown(
    """
    <style>
    .sig-white-panel {
        background: #ffffff;
        border: 1px solid rgba(15, 23, 42, 0.10);
        border-radius: 22px;
        padding: 1.1rem 1.1rem 1rem 1.1rem;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        margin-top: 0.2rem;
        margin-bottom: 1rem;
    }

    .sig-white-panel h2,
    .sig-white-panel h3,
    .sig-white-panel p,
    .sig-white-panel span,
    .sig-white-panel div,
    .sig-white-panel label {
        color: #0f172a !important;
    }

    .sig-white-panel .ui-divider {
        background: rgba(15, 23, 42, 0.12) !important;
    }

    .sig-white-panel div[data-testid="stDataFrame"] {
        background: #ffffff !important;
        border: 1px solid rgba(15, 23, 42, 0.10) !important;
        border-radius: 14px !important;
    }

    .sig-summary-box {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(15, 23, 42, 0.10);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
        color: #0f172a !important;
    }

    .sig-summary-box strong,
    .sig-summary-box span,
    .sig-summary-box div,
    .sig-summary-box p {
        color: #0f172a !important;
    }

    .sig-hint-box {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(59, 130, 246, 0.18);
        border-radius: 18px;
        padding: 1rem 1.05rem;
        margin-top: 0.55rem;
        margin-bottom: 0.9rem;
        color: #0f172a !important;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    }

    .sig-hint-box strong,
    .sig-hint-box span,
    .sig-hint-box div,
    .sig-hint-box p {
        color: #0f172a !important;
    }

    .sig-mini-meta {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.48rem 0.8rem;
        border-radius: 999px;
        background: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.30);
        color: #334155 !important;
        font-size: 0.84rem;
        font-weight: 700;
        margin-right: 0.45rem;
        margin-bottom: 0.45rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    .sig-mini-meta strong,
    .sig-mini-meta span,
    .sig-mini-meta div {
        color: #334155 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================
# HELPERS
# ==============================
def normalize_flags(flags: dict) -> dict:
    return {k: bool(v) for k, v in flags.items()}


def active_signals(flags: dict) -> list[str]:
    clean = normalize_flags(flags)
    return [SIGNAL_LABELS.get(k, k) for k, v in clean.items() if v]


def signal_table(flags: dict) -> pd.DataFrame:
    clean = normalize_flags(flags)
    return pd.DataFrame(
        {
            "Señal": [SIGNAL_LABELS.get(k, k) for k in clean.keys()],
            "Activa": ["Sí" if v else "No" for v in clean.values()],
        }
    )


def classify_signal_risk(signal: dict) -> dict:
    recommendation = str(signal.get("recommendation", "")).lower()
    score_buy = int(signal.get("score_buy", 0))
    score_sell = int(signal.get("score_sell", 0))
    reasons = signal.get("reasons", []) or []

    if "compra" in recommendation or score_buy >= score_sell + 2:
        return {
            "estado": "Favorable",
            "ui": "positive",
            "mensaje": "Predominan señales de fortaleza o entrada táctica de corto plazo.",
        }

    if "venta" in recommendation or score_sell >= score_buy + 2:
        return {
            "estado": "Desfavorable",
            "ui": "danger",
            "mensaje": "Predominan señales de deterioro técnico, agotamiento o presión bajista.",
        }

    if len(reasons) == 0 and score_buy == score_sell:
        return {
            "estado": "Neutral",
            "ui": "warning",
            "mensaje": "No hay una ventaja técnica clara; el activo luce en zona de espera.",
        }

    return {
        "estado": "Mixto / Precaución",
        "ui": "warning",
        "mensaje": "Existen señales mixtas o poco concluyentes entre tendencia, momentum y reversión.",
    }


def render_signal_card(item: dict, modo_actual: str):
    palettes = {
        "positive": {
            "bg": "linear-gradient(180deg, rgba(12,70,38,0.92) 0%, rgba(14,90,48,0.88) 100%)",
            "border": "rgba(74, 222, 128, 0.30)",
            "pill_bg": "rgba(255,255,255,0.16)",
            "pill_color": "#ffffff",
        },
        "warning": {
            "bg": "linear-gradient(180deg, rgba(97,63,13,0.92) 0%, rgba(120,78,18,0.88) 100%)",
            "border": "rgba(245, 158, 11, 0.32)",
            "pill_bg": "rgba(255,255,255,0.16)",
            "pill_color": "#ffffff",
        },
        "danger": {
            "bg": "linear-gradient(180deg, rgba(88,18,35,0.92) 0%, rgba(115,24,47,0.88) 100%)",
            "border": "rgba(251, 113, 133, 0.32)",
            "pill_bg": "rgba(255,255,255,0.16)",
            "pill_color": "#ffffff",
        },
    }

    style = palettes.get(item["ui"], palettes["warning"])
    badge_text = f"Modo {modo_actual}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}

            .sig-card {{
                background: {style["bg"]};
                border: 1px solid {style["border"]};
                border-radius: 20px;
                padding: 16px 16px 14px 16px;
                min-height: 290px;
                box-sizing: border-box;
                box-shadow: 0 12px 28px rgba(0,0,0,0.18);
            }}

            .top {{
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 8px;
            }}

            .asset {{
                font-size: 1rem;
                font-weight: 800;
                color: #ffffff;
                margin-bottom: 4px;
            }}

            .ticker {{
                font-size: 0.80rem;
                color: rgba(255,255,255,0.78);
            }}

            .mode-badge {{
                display: inline-flex;
                align-items: center;
                padding: 6px 10px;
                border-radius: 999px;
                background: rgba(255,255,255,0.14);
                border: 1px solid rgba(255,255,255,0.18);
                color: #ffffff;
                font-size: 0.74rem;
                font-weight: 800;
                white-space: nowrap;
            }}

            .pill {{
                display: inline-flex;
                align-items: center;
                padding: 6px 10px;
                border-radius: 999px;
                background: {style["pill_bg"]};
                color: {style["pill_color"]};
                border: 1px solid rgba(255,255,255,0.16);
                font-size: 0.80rem;
                font-weight: 800;
                margin-bottom: 10px;
            }}

            .subtitle {{
                font-size: 0.78rem;
                color: rgba(255,255,255,0.72);
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.03em;
                margin-bottom: 4px;
                margin-top: 8px;
            }}

            .text {{
                font-size: 0.87rem;
                color: #ffffff;
                line-height: 1.46;
                margin-bottom: 8px;
            }}

            .scores {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
                margin-top: 8px;
                margin-bottom: 8px;
            }}

            .score-box {{
                background: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 14px;
                padding: 10px 12px;
            }}

            .score-label {{
                font-size: 0.74rem;
                color: rgba(255,255,255,0.70);
                margin-bottom: 2px;
            }}

            .score-value {{
                font-size: 1.08rem;
                font-weight: 800;
                color: #ffffff;
            }}
        </style>
    </head>
    <body>
        <div class="sig-card">
            <div class="top">
                <div>
                    <div class="asset">{item['asset_name']}</div>
                    <div class="ticker">{item['ticker']}</div>
                </div>
                <div class="mode-badge">{badge_text}</div>
            </div>

            <div class="pill">{item['recommendation']}</div>

            <div class="subtitle">Semáforo</div>
            <div class="text"><strong>{item['semaforo_estado']}</strong> · {item['semaforo_msg']}</div>

            <div class="scores">
                <div class="score-box">
                    <div class="score-label">Score compra</div>
                    <div class="score-value">{item['score_buy']}</div>
                </div>
                <div class="score-box">
                    <div class="score-label">Score venta</div>
                    <div class="score-value">{item['score_sell']}</div>
                </div>
            </div>

            <div class="subtitle">Señales activas</div>
            <div class="text">{item['active_text']}</div>
        </div>
    </body>
    </html>
    """
    components.html(html, height=330)


# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 7 - Señales y alertas",
    "Resume señales técnicas por activo y las traduce en una lectura operativa más clara",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo resume señales técnicas por activo y las convierte en una lectura táctica rápida para apoyar la interpretación del portafolio."
    )
else:
    nota(
        "En modo estadístico, este bloque sintetiza señales provenientes de tendencia, reversión y momentum para priorización táctica de activos."
    )


# ==============================
# INTRODUCCIÓN
# ==============================
seccion("Resumen Del Módulo")

if modo == "General":
    nota(
        "Cada activo se resume en una tarjeta con recomendación, semáforo técnico, score de compra/venta y señales activas más relevantes."
    )
else:
    nota(
        "La recomendación final agrega evidencia de MACD, RSI, Bollinger, cruces de medias y oscilador estocástico para construir una lectura técnica por activo."
    )

st.markdown(
    f"""
    <div class="sig-hint-box">
        <strong>Interpretación del horizonte:</strong>
        el horizonte modifica la cantidad de historia usada para calcular los indicadores,
        pero la señal final reportada corresponde a la <strong>última fecha disponible</strong>
        dentro de la ventana seleccionada ({start_date} a {end_date}).
        Por eso, al cambiar el horizonte, algunas señales pueden mantenerse iguales si el tramo final del activo no cambia de forma relevante.
    </div>
    """,
    unsafe_allow_html=True,
)

meta_1, meta_2, meta_3 = st.columns(3)
with meta_1:
    st.markdown(
        f'<div class="sig-mini-meta"><strong>Horizonte:</strong>&nbsp;{horizonte}</div>',
        unsafe_allow_html=True,
    )
with meta_2:
    st.markdown(
        f'<div class="sig-mini-meta"><strong>Inicio:</strong>&nbsp;{start_date}</div>',
        unsafe_allow_html=True,
    )
with meta_3:
    st.markdown(
        f'<div class="sig-mini-meta"><strong>Fin:</strong>&nbsp;{end_date}</div>',
        unsafe_allow_html=True,
    )


# ==============================
# CONSTRUCCIÓN DE TARJETAS
# ==============================
cards_data = []

for asset_name, meta in ASSETS.items():
    ticker = meta["ticker"]
    df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))

    if df.empty:
        continue

    ind = compute_all_indicators(df)
    signal = evaluate_signals(
        ind,
        rsi_overbought=rsi_overbought,
        rsi_oversold=rsi_oversold,
        stoch_overbought=stoch_overbought,
        stoch_oversold=stoch_oversold,
    )

    if not signal:
        continue

    flags = normalize_flags(signal["details"])
    active = active_signals(flags)
    semaforo = classify_signal_risk(signal)

    cards_data.append(
        {
            "asset_name": asset_name,
            "ticker": ticker,
            "recommendation": signal.get("recommendation", "Sin recomendación"),
            "semaforo_estado": semaforo["estado"],
            "semaforo_msg": semaforo["mensaje"],
            "score_buy": signal.get("score_buy", 0),
            "score_sell": signal.get("score_sell", 0),
            "active_text": ", ".join(active) if active else "Ninguna",
            "flags": flags,
            "ui": semaforo["ui"],
        }
    )

if not cards_data:
    st.warning("No fue posible construir señales para los activos en la ventana seleccionada.")
    st.stop()

favorables = sum(1 for x in cards_data if x["semaforo_estado"] == "Favorable")
desfavorables = sum(1 for x in cards_data if x["semaforo_estado"] == "Desfavorable")
mixtas = len(cards_data) - favorables - desfavorables


# ==============================
# KPIS
# ==============================
seccion("KPIs Del Módulo")

k1, k2, k3, k4 = st.columns(4)

with k1:
    tarjeta_kpi(
        "Activos evaluados",
        str(len(cards_data)),
        help_text="Número de activos con señales válidas en la ventana analizada.",
    )

with k2:
    tarjeta_kpi(
        "Favorables",
        str(favorables),
        help_text="Activos donde predominan señales de compra o fortaleza.",
    )

with k3:
    tarjeta_kpi(
        "Desfavorables",
        str(desfavorables),
        help_text="Activos donde predominan señales de venta o deterioro técnico.",
    )

with k4:
    tarjeta_kpi(
        "Mixtos / neutrales",
        str(mixtas),
        help_text="Activos sin una ventaja técnica clara o con evidencia cruzada.",
    )

plot_card_footer(
    f"En la ventana analizada se identifican {favorables} activos favorables, {desfavorables} desfavorables y {mixtas} con lectura intermedia o no concluyente."
)


# ==============================
# TABS
# ==============================
tabs = st.tabs(
    [
        "Lectura por activo",
        "Detalle técnico",
        "Interpretación final",
    ]
)
tab1, tab2, tab3 = tabs


# ==============================
# TAB 1
# ==============================
with tab1:
    st.markdown('<div class="sig-white-panel">', unsafe_allow_html=True)

    seccion("Lectura Por Activo")

    for i in range(0, len(cards_data), 2):
        cols = st.columns(2)
        row_items = cards_data[i:i + 2]

        for col, item in zip(cols, row_items):
            with col:
                render_signal_card(item, modo)

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# TAB 2
# ==============================
with tab2:
    st.markdown('<div class="sig-white-panel">', unsafe_allow_html=True)

    seccion("Detalle Técnico Por Activo")

    if not mostrar_detalle:
        nota(
            "Activa la opción 'Mostrar detalle por activo' en la barra lateral si deseas desplegar el detalle completo de señales para cada activo."
        )
    else:
        for item in cards_data:
            with st.expander(f"Ver detalle de señales - {item['asset_name']}"):
                c1, c2 = st.columns([1, 1.2])

                with c1:
                    st.markdown(
                        f"""
                        <div class="sig-summary-box">
                            <strong>Recomendación:</strong> {item['recommendation']}<br><br>
                            <strong>Semáforo:</strong> {item['semaforo_estado']}<br><br>
                            <strong>Score compra:</strong> {item['score_buy']}<br>
                            <strong>Score venta:</strong> {item['score_sell']}<br><br>
                            <strong>Señales activas:</strong> {item['active_text']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.dataframe(
                        signal_table(item["flags"]),
                        use_container_width=True,
                        hide_index=True,
                    )

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# TAB 3
# ==============================
with tab3:
    st.markdown('<div class="sig-white-panel">', unsafe_allow_html=True)

    seccion("Interpretación Final")

    if modo == "General":
        if favorables > desfavorables:
            nota(
                f"En esta ventana predominan señales favorables ({favorables} activos), por lo que la lectura técnica agregada sugiere un sesgo más constructivo que defensivo. Aun así, conviene contrastar estas señales con riesgo, benchmark y contexto macro."
            )
        elif desfavorables > favorables:
            nota(
                f"En esta ventana predominan señales desfavorables ({desfavorables} activos), lo que sugiere mayor cautela táctica. Esto puede reflejar sobrecompra, pérdida de momentum o deterioro técnico en varios activos del portafolio."
            )
        else:
            nota(
                "La lectura agregada es mixta: hay señales favorables, desfavorables y neutrales coexistiendo. En este caso, el módulo sugiere prudencia y selección más cuidadosa por activo en vez de una lectura uniforme del portafolio."
            )
    else:
        nota(
            f"Desde una perspectiva agregada, el módulo identifica {favorables} activos con lectura favorable, {desfavorables} con lectura desfavorable y {mixtas} con lectura intermedia o no concluyente. Esto sugiere que las señales derivadas de momentum, reversión y tendencia no son homogéneas en todo el universo analizado y deben usarse como apoyo táctico, no como criterio aislado de asignación."
        )

    nota(
        "Metodológicamente, este módulo debe leerse como una fotografía técnica al cierre de la ventana seleccionada. El horizonte no redefine por sí mismo la fecha de evaluación; redefine la muestra histórica usada para calcular indicadores."
    )

    st.markdown("</div>", unsafe_allow_html=True)