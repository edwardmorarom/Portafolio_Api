import streamlit as st
import pandas as pd

from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import (
    header_dashboard,
    seccion,
    nota,
    tarjeta_kpi,
    plot_card_header,
    plot_card_footer,
)

from src.config import (
    APP_TITLE,
    ASSET_TICKERS,
    DEFAULT_END_DATE,
    DEFAULT_START_DATE,
    GLOBAL_BENCHMARK,
    ensure_project_dirs,
)
from src.download import load_market_bundle
from src.preprocess import (
    equal_weight_portfolio,
    annualize_return,
    annualize_volatility,
)
from src.plots import plot_normalized_prices


# ---------------------------------------------------------
# Configuración inicial
# ---------------------------------------------------------
ensure_project_dirs()

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Estilos locales de portada
# ---------------------------------------------------------
def inject_home_css():
    st.markdown(
        """
        <style>
        .home-info-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            min-height: 124px;
        }

        .home-info-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 900;
            color: #64748B !important;
            margin-bottom: 0.4rem;
        }

        .home-info-value {
            font-size: 0.98rem;
            font-weight: 700;
            color: #0F172A !important;
            line-height: 1.55;
            word-break: break-word;
        }

        .home-module-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.75rem;
            min-height: 112px;
        }

        .home-module-title {
            font-size: 0.96rem;
            font-weight: 900;
            color: #0F172A !important;
            margin-bottom: 0.28rem;
            line-height: 1.3;
        }

        .home-module-desc {
            font-size: 0.90rem;
            color: #334155 !important;
            line-height: 1.55;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def info_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="home-info-card">
            <div class="home-info-label">{label}</div>
            <div class="home-info-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def module_card(title: str, desc: str):
    st.markdown(
        f"""
        <div class="home-module-card">
            <div class="home-module-title">{title}</div>
            <div class="home-module-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_home_css()


# ---------------------------------------------------------
# Cache de datos
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_market_data(tickers, start, end):
    return load_market_bundle(tickers=tickers, start=start, end=end)


# ---------------------------------------------------------
# Setup global UI
# ---------------------------------------------------------
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Configuración General",
    filtros_expanded=False,
)

all_tickers = list(ASSET_TICKERS.values())


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
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
        key="app_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="app_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="app_end")

    selected_tickers = st.multiselect(
        "Selecciona activos",
        options=all_tickers,
        default=all_tickers[: min(5, len(all_tickers))],
        help="Escoge uno o varios activos para construir el análisis.",
        key="app_selected_tickers",
    )

    mostrar_estructura = st.checkbox("Mostrar estructura del dashboard", value=True, key="app_show_structure")
    mostrar_ultimos_precios = st.checkbox("Mostrar últimos precios", value=True, key="app_show_prices")


# ---------------------------------------------------------
# Validaciones
# ---------------------------------------------------------
if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

if not selected_tickers:
    st.warning("Selecciona al menos un activo para continuar.")
    st.stop()


# ---------------------------------------------------------
# Header principal
# ---------------------------------------------------------
header_dashboard(
    "RiskLab USTA - Dashboard de Riesgo Financiero",
    "Proyecto integrador con APIs, análisis técnico, VaR, GARCH, CAPM, Markowitz, señales y benchmark.",
    modo=modo,
)

if modo == "General":
    nota(
        "Panel de entrada al dashboard. Resume el universo de activos, el periodo de análisis y el comportamiento base del portafolio equiponderado."
    )
else:
    nota(
        "Síntesis del universo de análisis y caracterización inicial del portafolio equiponderado como referencia para los módulos cuantitativos."
    )


# ---------------------------------------------------------
# Configuración activa
# ---------------------------------------------------------
seccion("Configuración Activa")

cfg1, cfg2, cfg3 = st.columns([2.4, 1.1, 1.1])

with cfg1:
    st.markdown(
        f"""
        <div class="home-info-card">
            <div class="home-info-label">Activos y período</div>
            <div class="home-info-value">
                <strong>Activos:</strong> {" • ".join(selected_tickers)}<br><br>
                <strong>Período:</strong> {start_date} → {end_date}<br>
                <span style="color:#64748B; font-size:0.85rem;">Horizonte: {horizonte}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with cfg2:
    info_card(
        "Benchmark global",
        GLOBAL_BENCHMARK,
    )

with cfg3:
    info_card(
        "Modo activo",
        modo,
    )


# ---------------------------------------------------------
# Descarga de datos
# ---------------------------------------------------------
try:
    with st.spinner("Descargando datos de mercado..."):
        market_data = get_market_data(
            tickers=selected_tickers,
            start=str(start_date),
            end=str(end_date),
        )
except Exception as e:
    st.error(f"Ocurrió un error al descargar los datos: {e}")
    st.stop()

if market_data is None:
    st.error("No se recibieron datos del mercado.")
    st.stop()

if "close" not in market_data or market_data["close"].empty:
    st.error("No fue posible descargar precios. Verifica conexión, fechas o tickers.")
    st.stop()

if "returns" not in market_data or market_data["returns"].empty:
    st.error("No fue posible calcular rendimientos con los datos descargados.")
    st.stop()


# ---------------------------------------------------------
# Variables principales
# ---------------------------------------------------------
close_prices = market_data["close"]
returns = market_data["returns"]
portfolio_returns = equal_weight_portfolio(returns)

ann_return = annualize_return(portfolio_returns)
ann_vol = annualize_volatility(portfolio_returns)

obs_count = int(close_prices.shape[0])
asset_count = len(selected_tickers)

ret_delta = "Sesgo positivo" if ann_return > 0 else "Sesgo negativo" if ann_return < 0 else "Sin sesgo"
vol_delta = "Mayor dispersión" if ann_vol > 0.20 else "Dispersión moderada"


# ---------------------------------------------------------
# KPIs
# ---------------------------------------------------------
seccion("KPIs Del Portafolio")

k1, k2, k3, k4 = st.columns(4)

with k1:
    tarjeta_kpi(
        "Activos",
        str(asset_count),
        help_text="Cantidad de activos incluidos actualmente en el análisis.",
        subtexto="Universo usado para construir el portafolio equiponderado.",
    )

with k2:
    tarjeta_kpi(
        "Observaciones",
        str(obs_count),
        help_text="Número de precios disponibles en la muestra descargada.",
        subtexto="Base temporal utilizada para retornos y visualización.",
    )

with k3:
    tarjeta_kpi(
        "Retorno anualizado",
        f"{ann_return:.2%}",
        delta=ret_delta,
        help_text="Retorno estimado del portafolio equiponderado.",
        subtexto="Medida agregada de crecimiento esperado bajo anualización.",
    )

with k4:
    tarjeta_kpi(
        "Volatilidad anualizada",
        f"{ann_vol:.2%}",
        delta=vol_delta,
        help_text="Riesgo agregado estimado del portafolio.",
        subtexto="Dispersión anualizada de los rendimientos del portafolio.",
    )


# ---------------------------------------------------------
# Gráfico + resumen juntos
# ---------------------------------------------------------
seccion("Vista General Del Portafolio")

left_col, right_col = st.columns([1.7, 1], gap="large")

with left_col:
    plot_card_header(
        "Precios normalizados (base 100)",
        "Comparación relativa del desempeño de los activos desde una base común.",
        modo=modo,
        caption="Permite identificar rápidamente qué activos tuvieron mejor trayectoria relativa en el periodo.",
    )

    fig = plot_normalized_prices(close_prices)
    st.plotly_chart(fig, use_container_width=True)

    plot_card_footer(
        "Todos los activos parten de una base comparable, lo que facilita contrastar trayectorias y desempeño relativo."
    )

with right_col:
    plot_card_header(
        "Resumen del portafolio equiponderado",
        "Métricas descriptivas básicas del portafolio construido con pesos iguales.",
        modo=modo,
        caption="Complementa la lectura visual del gráfico con medidas agregadas.",
    )

    summary = pd.DataFrame(
        {
            "Métrica": [
                "Retorno anualizado",
                "Volatilidad anualizada",
                "Promedio diario",
                "Desviación estándar diaria",
            ],
            "Valor": [
                f"{ann_return:.2%}",
                f"{ann_vol:.2%}",
                f"{portfolio_returns.mean():.4%}",
                f"{portfolio_returns.std(ddof=1):.4%}",
            ],
        }
    )

    st.dataframe(summary, use_container_width=True, hide_index=True)

    plot_card_footer(
        "Este resumen concentra las medidas más útiles para una primera lectura del perfil riesgo-retorno."
    )


# ---------------------------------------------------------
# Últimos precios
# ---------------------------------------------------------
if mostrar_ultimos_precios:
    seccion("Últimos Precios Disponibles")
    st.dataframe(
        close_prices.tail(10).style.format("{:.2f}"),
        use_container_width=True,
    )


# ---------------------------------------------------------
# Estructura del dashboard
# ---------------------------------------------------------
if mostrar_estructura:
    seccion("Estructura Del Dashboard")

    m1, m2 = st.columns(2, gap="large")

    with m1:
        module_card(
            "00 Contextualización",
            "Presenta el sentido económico del portafolio, el papel de cada empresa y la lógica estratégica de la selección de activos.",
        )
        module_card(
            "01 Técnico",
            "Analiza precios e indicadores por activo para identificar tendencia, momentum, cruces relevantes y zonas de seguimiento.",
        )
        module_card(
            "02 Rendimientos",
            "Resume comportamiento estadístico de los retornos, dispersión, extremos y contraste con supuestos de normalidad.",
        )
        module_card(
            "03 GARCH",
            "Modela volatilidad condicional para estudiar persistencia del riesgo y pronósticos dinámicos de incertidumbre.",
        )
        module_card(
            "04 CAPM",
            "Evalúa sensibilidad frente al mercado, beta, alpha y retorno esperado bajo el marco clásico de riesgo sistemático.",
        )

    with m2:
        module_card(
            "05 VaR / CVaR",
            "Cuantifica riesgo extremo del portafolio mediante pérdida umbral y pérdida media en escenarios severos.",
        )
        module_card(
            "06 Markowitz",
            "Construye frontera eficiente y compara portafolios óptimos bajo criterios de mínima varianza, Sharpe y retorno objetivo.",
        )
        module_card(
            "07 Señales",
            "Integra reglas de lectura operativa para resumir alertas y condiciones de seguimiento por activo.",
        )
        module_card(
            "08 Macro y Benchmark",
            "Conecta el análisis del portafolio con contexto macroeconómico y comparación frente a índices de referencia.",
        )
        module_card(
            "09 Panel de decisión",
            "Integra resultados de los módulos anteriores para construir una lectura final y apoyar la postura de análisis.",
        )