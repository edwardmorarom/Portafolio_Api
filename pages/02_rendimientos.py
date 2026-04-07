import streamlit as st

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, get_ticker, ensure_project_dirs
from src.download import download_single_ticker
from src.returns_analysis import (
    compute_return_series,
    descriptive_stats,
    normality_tests,
    qq_plot_data,
    stylized_facts_comment,
)
from src.plots import plot_histogram_with_normal, plot_qq, plot_box

ensure_project_dirs()
st.title("Módulo 2 - Rendimientos y propiedades empíricas")

with st.sidebar:
    st.header("Parámetros")
    asset_name = st.selectbox("Activo", list(ASSETS.keys()), index=0)
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="ret_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="ret_end")
    return_type = st.radio("Tipo de retorno", ["simple_return", "log_return"], index=1)

ticker = get_ticker(asset_name)
df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))

if df.empty:
    st.error("No se pudieron descargar datos.")
    st.stop()

ret_df = compute_return_series(df["Adj Close"] if "Adj Close" in df.columns else df["Close"])
series = ret_df[return_type]

st.subheader(f"{asset_name} ({ticker})")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Estadísticos descriptivos")
    st.dataframe(descriptive_stats(series), width="stretch")

with col2:
    st.markdown("#### Pruebas de normalidad")
    st.dataframe(normality_tests(series), width="stretch")

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(plot_histogram_with_normal(series), width="stretch")
with col4:
    st.plotly_chart(plot_box(series), width="stretch")

st.plotly_chart(plot_qq(qq_plot_data(series)), width="stretch")

st.subheader("Interpretación")
st.write(stylized_facts_comment(series))

st.subheader("Últimos rendimientos")
st.dataframe(ret_df.tail(15), width="stretch")
