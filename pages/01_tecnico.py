import streamlit as st

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, get_ticker, ensure_project_dirs
from src.download import download_single_ticker
from src.indicators import compute_all_indicators
from src.plots import (
    plot_price_and_mas,
    plot_bollinger,
    plot_rsi,
    plot_macd,
    plot_stochastic,
)

ensure_project_dirs()
st.title("Módulo 1 - Análisis técnico")

with st.sidebar:
    st.header("Parámetros técnicos")
    asset_name = st.selectbox("Activo", list(ASSETS.keys()), index=0)
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="tec_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="tec_end")
    sma_window = st.slider("Ventana SMA", min_value=5, max_value=60, value=20)
    ema_window = st.slider("Ventana EMA", min_value=5, max_value=60, value=20)
    rsi_window = st.slider("Ventana RSI", min_value=5, max_value=30, value=14)
    bb_window = st.slider("Ventana Bollinger", min_value=10, max_value=60, value=20)
    stoch_window = st.slider("Ventana Estocástico", min_value=5, max_value=30, value=14)

ticker = get_ticker(asset_name)
df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))

if df.empty:
    st.error("No se pudieron descargar datos del activo seleccionado.")
    st.stop()

ind = compute_all_indicators(
    df,
    sma_window=sma_window,
    ema_window=ema_window,
    rsi_window=rsi_window,
    bb_window=bb_window,
    stoch_window=stoch_window,
)

st.subheader(f"{asset_name} ({ticker})")
st.plotly_chart(plot_price_and_mas(ind, sma_col=f"SMA_{sma_window}", ema_col=f"EMA_{ema_window}"), width="stretch")
st.info("SMA y EMA ayudan a visualizar tendencia. La EMA reacciona más rápido a cambios recientes.")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_bollinger(ind), width="stretch")
    st.info("Las Bandas de Bollinger muestran dispersión alrededor de la media móvil.")
with col2:
    st.plotly_chart(plot_rsi(ind, rsi_col=f"RSI_{rsi_window}"), width="stretch")
    st.info("RSI mayor a 70 puede sugerir sobrecompra; menor a 30, sobreventa.")

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(plot_macd(ind), width="stretch")
    st.info("MACD ayuda a detectar cambios de momentum y cruces de señal.")
with col4:
    st.plotly_chart(plot_stochastic(ind), width="stretch")
    st.info("El Estocástico compara el cierre actual con el rango reciente del precio.")

st.subheader("Últimos datos con indicadores")
st.dataframe(ind.tail(15), width="stretch")
