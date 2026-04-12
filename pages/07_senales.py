import pandas as pd
import streamlit as st

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import download_single_ticker
from src.indicators import compute_all_indicators
from src.signals import evaluate_signals

ensure_project_dirs()
st.title("Módulo 7 - Señales y alertas")


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
    """
    Construye un semáforo simple para apoyar la interpretación del activo.
    No reemplaza análisis financiero integral; es una guía visual.
    """
    recommendation = str(signal.get("recommendation", "")).lower()
    score_buy = int(signal.get("score_buy", 0))
    score_sell = int(signal.get("score_sell", 0))
    reasons = signal.get("reasons", []) or []

    if "compra" in recommendation or score_buy >= score_sell + 2:
        return {
            "emoji": "🟢",
            "estado": "Favorable",
            "color": "green",
            "mensaje": (
                "Las señales técnicas favorecen una entrada o una visión constructiva del activo. "
                "Aun así, conviene confirmar con contexto macro, riesgo y horizonte de inversión."
            ),
        }

    if "venta" in recommendation or score_sell >= score_buy + 2:
        return {
            "emoji": "🔴",
            "estado": "Desfavorable",
            "color": "red",
            "mensaje": (
                "Las señales activas sugieren presión bajista, sobrecompra o deterioro técnico. "
                "No luce como un punto atractivo de entrada de corto plazo."
            ),
        }

    if len(reasons) == 0 and score_buy == score_sell:
        return {
            "emoji": "🟡",
            "estado": "Neutral",
            "color": "yellow",
            "mensaje": (
                "No hay una ventaja técnica clara. El activo luce en zona de espera o sin señales extremas."
            ),
        }

    return {
        "emoji": "🟡",
        "estado": "Mixto / Precaución",
        "color": "yellow",
        "mensaje": (
            "Existen señales mixtas o poco concluyentes. Puede haber conflicto entre impulso, reversión y tendencia."
        ),
    }


with st.sidebar:
    st.header("Umbrales configurables")
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="sig_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="sig_end")
    rsi_overbought = st.slider("RSI sobrecompra", min_value=60, max_value=90, value=70)
    rsi_oversold = st.slider("RSI sobreventa", min_value=10, max_value=40, value=30)
    stoch_overbought = st.slider("Estocástico sobrecompra", min_value=60, max_value=95, value=80)
    stoch_oversold = st.slider("Estocástico sobreventa", min_value=5, max_value=40, value=20)

st.markdown(
    """
    Este módulo resume señales técnicas sobre cada activo y las traduce a una lectura operativa.
    
    **Semáforo interpretativo:**
    - **🟢 Favorable**: predominan señales de entrada o fortaleza técnica.
    - **🟡 Neutral / Precaución**: señales mixtas, débiles o sin ventaja clara.
    - **🔴 Desfavorable**: predominan señales de venta, agotamiento o deterioro técnico.
    
    **Importante:** este semáforo no garantiza rentabilidad y no reemplaza análisis de riesgo,
    benchmark, VaR, GARCH ni contexto macroeconómico.
    """
)

for asset_name, meta in ASSETS.items():
    ticker = meta["ticker"]
    df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))

    if df.empty:
        st.warning(f"No se pudieron descargar datos para {asset_name}.")
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

    with st.container(border=True):
        st.subheader(f"{asset_name} ({ticker})")

        # Recomendación principal
        if signal["color"] == "green":
            st.success(f"Recomendación: {signal['recommendation']}")
        elif signal["color"] == "red":
            st.error(f"Recomendación: {signal['recommendation']}")
        else:
            st.warning(f"Recomendación: {signal['recommendation']}")

        # Semáforo ejecutivo
        st.markdown(f"### {semaforo['emoji']} Semáforo: {semaforo['estado']}")

        if semaforo["color"] == "green":
            st.success(semaforo["mensaje"])
        elif semaforo["color"] == "red":
            st.error(semaforo["mensaje"])
        else:
            st.warning(semaforo["mensaje"])

        st.write(f"**Score compra:** {signal['score_buy']} | **Score venta:** {signal['score_sell']}")
        st.write(
            f"**Razones:** {', '.join(signal['reasons']) if signal['reasons'] else 'Sin señales extremas activas.'}"
        )
        st.write(f"**Señales activas:** {', '.join(active) if active else 'Ninguna'}")

        with st.expander("Ver detalle de señales"):
            st.dataframe(signal_table(flags), width="stretch", hide_index=True)