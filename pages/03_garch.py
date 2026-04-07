import streamlit as st

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, get_ticker, ensure_project_dirs
from src.download import download_single_ticker
from src.returns_analysis import compute_return_series
from src.garch_models import fit_garch_models
from src.plots import plot_volatility, plot_forecast

ensure_project_dirs()
st.title("Módulo 3 - Modelos ARCH/GARCH")

with st.sidebar:
    st.header("Parámetros GARCH")
    asset_name = st.selectbox("Activo representativo", list(ASSETS.keys()), index=0)
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="garch_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="garch_end")

ticker = get_ticker(asset_name)
df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))

if df.empty:
    st.error("No se pudieron descargar datos.")
    st.stop()

ret_df = compute_return_series(df["Adj Close"] if "Adj Close" in df.columns else df["Close"])
results = fit_garch_models(ret_df["log_return"])

if results["comparison"].empty:
    st.warning("No hay suficientes datos para ajustar los modelos GARCH.")
    st.stop()

st.markdown(
    """
    La volatilidad condicional se usa cuando la varianza no es constante en el tiempo.
    En finanzas esto ocurre con frecuencia por clustering de volatilidad.
    """
)

st.subheader("Comparación de modelos")
st.dataframe(results["comparison"], width="stretch")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_volatility(results["volatility"]), width="stretch")
with col2:
    st.plotly_chart(plot_forecast(results["forecast"]), width="stretch")

st.subheader("Diagnóstico")
st.dataframe(results["diagnostics"], width="stretch")

st.subheader("Residuos estandarizados")
st.dataframe(results["std_resid"].tail(20), width="stretch")
