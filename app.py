import streamlit as st
import pandas as pd

from src.config import (
    APP_TITLE,
    APP_SUBTITLE,
    ASSET_TICKERS,
    DEFAULT_END_DATE,
    DEFAULT_START_DATE,
    GLOBAL_BENCHMARK,
    ensure_project_dirs,
)
from src.download import load_market_bundle
from src.preprocess import equal_weight_portfolio, annualize_return, annualize_volatility
from src.plots import plot_normalized_prices

ensure_project_dirs()

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

st.markdown(
    """
    Este tablero implementa el Proyecto Integrador de Teoría del Riesgo con:
    indicadores técnicos, rendimientos, modelos GARCH, CAPM, VaR/CVaR,
    optimización de Markowitz, señales de trading y contexto macro/benchmark.
    """
)

with st.sidebar:
    st.header("Configuración general")
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE)
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE)
    st.info(
        "La navegación entre módulos se hace desde la barra lateral de Streamlit "
        "usando la carpeta `pages/`."
    )

tickers = list(ASSET_TICKERS.values())
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))

if bundle["close"].empty:
    st.error("No fue posible descargar precios. Verifica conexión o tickers.")
    st.stop()

close_prices = bundle["close"]
returns = bundle["returns"]
portfolio_returns = equal_weight_portfolio(returns)

col1, col2, col3 = st.columns(3)
col1.metric("Número de activos", len(tickers))
col2.metric("Observaciones de precios", int(close_prices.shape[0]))
col3.metric("Benchmark global", GLOBAL_BENCHMARK)

st.subheader("Precios normalizados (base 100)")
fig_norm = plot_normalized_prices(close_prices)
st.plotly_chart(fig_norm, width="stretch")

st.subheader("Resumen rápido del portafolio equiponderado")
summary = pd.DataFrame(
    {
        "Métrica": [
            "Rendimiento anualizado",
            "Volatilidad anualizada",
            "Promedio diario",
            "Desviación estándar diaria",
        ],
        "Valor": [
            annualize_return(portfolio_returns),
            annualize_volatility(portfolio_returns),
            portfolio_returns.mean(),
            portfolio_returns.std(ddof=1),
        ],
    }
)
st.dataframe(summary, width="stretch")

st.subheader("Últimos precios disponibles")
st.dataframe(close_prices.tail(10), width="stretch")

st.markdown(
    """
    ### Estructura del dashboard
    - **01 Técnico:** indicadores y gráficos por activo.
    - **02 Rendimientos:** estadística descriptiva y pruebas de normalidad.
    - **03 GARCH:** comparación de modelos de volatilidad.
    - **04 CAPM:** beta, CAPM y benchmark local.
    - **05 VaR/CVaR:** riesgo del portafolio con 3 métodos.
    - **06 Markowitz:** frontera eficiente y portafolios óptimos.
    - **07 Señales:** alertas automáticas de trading.
    - **08 Macro y benchmark:** contexto macro y comparación contra índice global.
    """
)
