import streamlit as st
import numpy as np

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import load_market_bundle
from src.preprocess import equal_weight_vector, equal_weight_portfolio
from src.risk_metrics import risk_comparison_table
from src.plots import plot_var_distribution

ensure_project_dirs()
st.title("Módulo 5 - VaR y CVaR")

with st.sidebar:
    st.header("Parámetros de riesgo")
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="var_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="var_end")
    alpha = st.selectbox("Nivel de confianza", [0.95, 0.99], index=0)
    n_sim = st.slider("Simulaciones Monte Carlo", min_value=5000, max_value=50000, value=10000, step=5000)

tickers = [meta["ticker"] for meta in ASSETS.values()]
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))
returns = bundle["returns"].dropna()

if returns.empty:
    st.error("No hay datos de retornos para construir el portafolio.")
    st.stop()

weights = equal_weight_vector(returns.shape[1])
portfolio_returns = equal_weight_portfolio(returns)

table = risk_comparison_table(
    portfolio_returns=portfolio_returns,
    asset_returns_df=returns,
    weights=weights,
    alpha=alpha,
    n_sim=n_sim,
)

st.subheader("Portafolio equiponderado")
st.write("Pesos:", dict(zip(returns.columns, np.round(weights, 4))))

st.subheader("Comparación VaR / CVaR")
st.dataframe(table, width="stretch")

st.plotly_chart(plot_var_distribution(portfolio_returns, table), width="stretch")

st.info(
    "El VaR estima una pérdida umbral; el CVaR mide la pérdida promedio en la cola más extrema."
)
