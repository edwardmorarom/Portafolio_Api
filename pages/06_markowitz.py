import numpy as np
import streamlit as st

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import load_market_bundle
from src.markowitz import (
    simulate_portfolios,
    efficient_frontier,
    minimum_variance_portfolio,
    maximum_sharpe_portfolio,
    weights_table,
)
from src.plots import plot_correlation_heatmap, plot_frontier
from src.api.macro import macro_snapshot

ensure_project_dirs()
st.title("Módulo 6 - Optimización de portafolio (Markowitz)")

with st.sidebar:
    st.header("Parámetros de optimización")
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="mk_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="mk_end")
    n_portfolios = st.slider("Número de portafolios", min_value=5000, max_value=50000, value=10000, step=5000)

tickers = [meta["ticker"] for meta in ASSETS.values()]
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))

returns = (
    bundle["returns"]
    .replace([np.inf, -np.inf], np.nan)
    .dropna(how="any")
)

if returns.empty or returns.shape[0] < 2 or returns.shape[1] < 2:
    st.error("No hay suficientes datos de retornos alineados para ejecutar Markowitz.")
    st.write({
        "shape_returns": bundle["returns"].shape,
        "na_por_activo": bundle["returns"].isna().sum().to_dict(),
    })
    st.stop()

macro = macro_snapshot()
rf_annual = (
    macro["risk_free_rate_pct"] / 100
    if macro["risk_free_rate_pct"] == macro["risk_free_rate_pct"]
    else 0.03
)

corr = returns.corr()
st.subheader("Matriz de correlación")
st.plotly_chart(plot_correlation_heatmap(corr), width="stretch")

sim_df = simulate_portfolios(returns, rf_annual=rf_annual, n_portfolios=n_portfolios)

if sim_df.empty:
    st.error("La simulación de portafolios no generó resultados válidos.")
    st.write({
        "shape_returns_filtrado": returns.shape,
        "rf_annual": rf_annual,
        "n_portfolios": n_portfolios,
    })
    st.stop()

frontier_df = efficient_frontier(sim_df)
min_var = minimum_variance_portfolio(sim_df)
max_sharpe = maximum_sharpe_portfolio(sim_df)

if min_var.empty or max_sharpe.empty:
    st.error("No fue posible identificar los portafolios óptimos.")
    st.stop()

st.plotly_chart(plot_frontier(sim_df, frontier_df, min_var, max_sharpe), width="stretch")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Portafolio de mínima varianza")
    st.dataframe(weights_table(min_var), width="stretch")

with col2:
    st.subheader("Portafolio de máximo Sharpe")
    st.dataframe(weights_table(max_sharpe), width="stretch")
