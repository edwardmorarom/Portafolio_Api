import streamlit as st
import pandas as pd

from src.config import (
    ASSETS,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    get_ticker,
    get_local_benchmark,
    ensure_project_dirs,
)
from src.download import download_single_ticker
from src.returns_analysis import compute_return_series
from src.capm import compute_beta_and_capm
from src.api.macro import macro_snapshot
from src.plots import plot_scatter_regression

ensure_project_dirs()
st.title("Módulo 4 - CAPM y Beta")

with st.sidebar:
    st.header("Parámetros CAPM")
    asset_name = st.selectbox("Activo", list(ASSETS.keys()), index=0)
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="capm_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="capm_end")

ticker = get_ticker(asset_name)
benchmark_ticker = get_local_benchmark(asset_name)

asset_df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))
bench_df = download_single_ticker(ticker=benchmark_ticker, start=str(start_date), end=str(end_date))

if asset_df.empty or bench_df.empty:
    st.error("No se pudieron descargar los datos del activo o del benchmark.")
    st.stop()

asset_ret = compute_return_series(asset_df["Adj Close"] if "Adj Close" in asset_df.columns else asset_df["Close"])["simple_return"]
bench_ret = compute_return_series(bench_df["Adj Close"] if "Adj Close" in bench_df.columns else bench_df["Close"])["simple_return"]

macro = macro_snapshot()
rf_annual = macro["risk_free_rate_pct"] / 100 if macro["risk_free_rate_pct"] == macro["risk_free_rate_pct"] else 0.03
res = compute_beta_and_capm(asset_ret, bench_ret, rf_annual=rf_annual)

if not res:
    st.warning("No hay suficientes datos alineados para CAPM.")
    st.stop()

st.subheader(f"{asset_name} ({ticker}) vs benchmark local ({benchmark_ticker})")

summary_df = pd.DataFrame(
    {
        "metric": [
            "beta",
            "alpha_diaria",
            "r_squared",
            "p_value_beta",
            "expected_return_capm_annual",
            "classification",
        ],
        "value": [
            res["beta"],
            res["alpha_diaria"],
            res["r_squared"],
            res["p_value_beta"],
            res["expected_return_capm_annual"],
            res["classification"],
        ],
    }
)

summary_df["value"] = summary_df["value"].astype(str)

st.dataframe(summary_df, width="stretch")

fig = plot_scatter_regression(
    x=res["scatter_data"]["market_excess"],
    y=res["scatter_data"]["asset_excess"],
    yhat=res["regression_line"]["y"],
    title="Regresión CAPM",
)
st.plotly_chart(fig, width="stretch")

st.info(
    "Beta > 1 sugiere mayor sensibilidad al mercado; Beta < 1 sugiere comportamiento más defensivo."
)
