from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import load_market_bundle, download_single_ticker
from src.preprocess import equal_weight_vector, equal_weight_portfolio
from src.risk_metrics import risk_comparison_table, validar_serie_para_garch
from src.garch_models import fit_garch_models
from src.benchmark import benchmark_summary
from src.indicators import compute_all_indicators
from src.signals import evaluate_signals

# Macro opcional: si falla, usamos fallback
try:
    from src.api.macro import macro_snapshot
except Exception:
    macro_snapshot = None

ensure_project_dirs()
st.title("Panel de decisión del portafolio")

with st.sidebar:
    st.header("Parámetros")
    start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="decision_start")
    end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="decision_end")
    alpha = st.selectbox("Nivel de confianza VaR", [0.95, 0.99], index=0, key="decision_alpha")
    n_sim = st.slider(
        "Simulaciones Monte Carlo",
        min_value=5000,
        max_value=50000,
        value=10000,
        step=5000,
        key="decision_nsim",
    )

# ==============================
# Helpers
# ==============================
def _get_rf_annual() -> float:
    if macro_snapshot is not None:
        try:
            snap = macro_snapshot()
            rf_pct = snap.get("risk_free_rate_pct", 3.0)
            return float(rf_pct) / 100.0
        except Exception:
            return 0.03
    return 0.03


def _signal_bucket(recommendation: str) -> str:
    txt = str(recommendation).lower()
    if "compra" in txt:
        return "favorable"
    if "venta" in txt:
        return "desfavorable"
    return "neutral"


def _build_signal_summary(start_date, end_date) -> dict:
    favorables = 0
    neutrales = 0
    desfavorables = 0
    detalle = []

    for asset_name, meta in ASSETS.items():
        ticker = meta["ticker"]
        try:
            df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))
            if df.empty:
                continue

            ind = compute_all_indicators(df)
            signal = evaluate_signals(ind)

            if not signal:
                continue

            bucket = _signal_bucket(signal.get("recommendation", ""))
            if bucket == "favorable":
                favorables += 1
            elif bucket == "desfavorable":
                desfavorables += 1
            else:
                neutrales += 1

            detalle.append(
                {
                    "activo": asset_name,
                    "ticker": ticker,
                    "recomendacion": signal.get("recommendation", "Sin señal"),
                    "score_compra": signal.get("score_buy", 0),
                    "score_venta": signal.get("score_sell", 0),
                }
            )
        except Exception:
            continue

    total = favorables + neutrales + desfavorables

    if total == 0:
        lectura = "Sin lectura disponible"
    elif favorables > desfavorables:
        lectura = "Sesgo técnico favorable"
    elif desfavorables > favorables:
        lectura = "Sesgo técnico desfavorable"
    else:
        lectura = "Sesgo técnico mixto"

    return {
        "favorables": favorables,
        "neutrales": neutrales,
        "desfavorables": desfavorables,
        "lectura": lectura,
        "detalle": pd.DataFrame(detalle),
    }


def _classify_risk(var_hist: float, persistencia: float, max_dd: float) -> tuple[str, str]:
    """
    Devuelve (nivel, mensaje)
    max_dd viene negativo; usamos magnitud absoluta.
    """
    dd_abs = abs(max_dd) if pd.notna(max_dd) else np.nan

    puntos = 0

    if pd.notna(var_hist):
        if var_hist >= 0.03:
            puntos += 2
        elif var_hist >= 0.015:
            puntos += 1

    if pd.notna(persistencia):
        if persistencia >= 0.98:
            puntos += 2
        elif persistencia >= 0.90:
            puntos += 1

    if pd.notna(dd_abs):
        if dd_abs >= 0.25:
            puntos += 2
        elif dd_abs >= 0.10:
            puntos += 1

    if puntos >= 5:
        return "Alto", "El portafolio muestra un perfil de riesgo alto por pérdidas extremas potenciales, persistencia de volatilidad y/o drawdown elevado."
    if puntos >= 3:
        return "Medio", "El portafolio muestra un perfil de riesgo intermedio; conviene vigilar la volatilidad y la exposición agregada."
    return "Bajo", "El portafolio muestra un perfil de riesgo relativamente controlado para la ventana analizada."


def _classify_benchmark(summary_df: pd.DataFrame, extras_df: pd.DataFrame) -> tuple[str, str]:
    if summary_df.empty:
        return "Sin benchmark", "No fue posible comparar el portafolio frente al benchmark."

    try:
        port_ret = float(summary_df.loc[summary_df["serie"] == "Portafolio", "ret_anualizado"].iloc[0])
        bench_ret = float(summary_df.loc[summary_df["serie"] == "Benchmark", "ret_anualizado"].iloc[0])
        alpha = float(extras_df.loc[extras_df["métrica"] == "Alpha de Jensen", "valor"].iloc[0]) if not extras_df.empty else np.nan

        if port_ret > bench_ret and (pd.isna(alpha) or alpha >= 0):
            return "Superior", "El portafolio supera al benchmark en retorno anualizado y mantiene una lectura comparativa favorable."
        if port_ret < bench_ret and (pd.isna(alpha) or alpha < 0):
            return "Inferior", "El portafolio viene rezagado frente al benchmark en la ventana analizada."
        return "Mixto", "La comparación con el benchmark es mixta: conviene revisar retorno, alpha y consistencia temporal."
    except Exception:
        return "Sin benchmark", "No fue posible construir una lectura robusta frente al benchmark."


def _final_decision(risk_level: str, signal_view: str, bench_view: str) -> tuple[str, str]:
    signal_low = signal_view.lower()
    bench_low = bench_view.lower()

    if risk_level == "Alto" and ("desfavorable" in signal_low or "mixto" in signal_low):
        return (
            "Postura defensiva",
            "La combinación de riesgo alto y señales poco favorables sugiere prudencia. No parece el mejor punto para aumentar exposición."
        )

    if risk_level == "Medio" and "favorable" in signal_low and "superior" in bench_low:
        return (
            "Entrada selectiva",
            "El contexto es razonable para mantener o aumentar exposición de forma selectiva, vigilando el riesgo."
        )

    if risk_level == "Bajo" and "favorable" in signal_low:
        return (
            "Lectura favorable",
            "El portafolio combina señales técnicas razonables con un perfil de riesgo más controlado."
        )

    return (
        "Postura neutral",
        "La lectura integrada no muestra una ventaja suficientemente clara. Conviene mantener disciplina y esperar mejor confirmación."
    )


# ==============================
# Carga de mercado
# ==============================
tickers = [meta["ticker"] for meta in ASSETS.values()]
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))

returns = bundle["returns"].replace([np.inf, -np.inf], np.nan).dropna()

if returns.empty or len(returns) < 30:
    st.error("No hay suficientes datos para construir el panel de decisión.")
    st.stop()

weights = equal_weight_vector(returns.shape[1])
portfolio_returns = equal_weight_portfolio(returns)

rf_annual = _get_rf_annual()

# ==============================
# Riesgo extremo
# ==============================
risk_table = risk_comparison_table(
    portfolio_returns=portfolio_returns,
    asset_returns_df=returns,
    weights=weights,
    alpha=alpha,
    n_sim=n_sim,
)

var_hist = np.nan
cvar_hist = np.nan
if not risk_table.empty and "Histórico" in risk_table["método"].values:
    row_hist = risk_table.loc[risk_table["método"] == "Histórico"].iloc[0]
    var_hist = float(row_hist["VaR_diario"])
    cvar_hist = float(row_hist["CVaR_diario"])

# ==============================
# GARCH sobre retorno del portafolio
# ==============================
garch_validation = validar_serie_para_garch(portfolio_returns, min_obs=120, max_null_ratio=0.05)
garch_results = {
    "comparison": pd.DataFrame(),
    "diagnostics": pd.DataFrame(),
    "best_model_name": None,
    "summary_text": "",
}
persistencia = np.nan

if garch_validation["ok"]:
    serie_garch = garch_validation["serie_limpia"] * 100.0
    garch_results = fit_garch_models(serie_garch)

    if not garch_results["diagnostics"].empty:
        persist_row = garch_results["diagnostics"].loc[
            garch_results["diagnostics"]["metrica"] == "persistencia_alpha_mas_beta"
        ]
        if not persist_row.empty:
            persistencia = pd.to_numeric(persist_row["valor"], errors="coerce").iloc[0]

# ==============================
# Benchmark
# ==============================
summary_df = pd.DataFrame()
extras_df = pd.DataFrame()
cum_port = pd.Series(dtype=float)
cum_bench = pd.Series(dtype=float)

try:
    bench_df = yf.download("^GSPC", start=str(start_date), end=str(end_date), auto_adjust=False)

    if bench_df.empty:
        benchmark_returns = pd.Series(dtype=float)
    else:
        if isinstance(bench_df.columns, pd.MultiIndex):
            if ("Adj Close", "^GSPC") in bench_df.columns:
                benchmark_prices = bench_df[("Adj Close", "^GSPC")]
            elif ("Close", "^GSPC") in bench_df.columns:
                benchmark_prices = bench_df[("Close", "^GSPC")]
            else:
                benchmark_prices = pd.Series(dtype=float)
        else:
            if "Adj Close" in bench_df.columns:
                benchmark_prices = bench_df["Adj Close"]
            elif "Close" in bench_df.columns:
                benchmark_prices = bench_df["Close"]
            else:
                benchmark_prices = pd.Series(dtype=float)

        benchmark_prices = pd.to_numeric(benchmark_prices, errors="coerce").dropna()
        benchmark_returns = benchmark_prices.pct_change().dropna()

except Exception as e:
    st.error(f"Error cargando benchmark: {e}")
    benchmark_returns = pd.Series(dtype=float)

if not benchmark_returns.empty:
    summary_df, extras_df, cum_port, cum_bench = benchmark_summary(
        portfolio_returns=portfolio_returns,
        benchmark_returns=benchmark_returns,
        rf_annual=rf_annual,
    )

max_dd = np.nan
if not summary_df.empty:
    try:
        max_dd = float(summary_df.loc[summary_df["serie"] == "Portafolio", "max_drawdown"].iloc[0])
    except Exception:
        max_dd = np.nan

benchmark_level, benchmark_msg = _classify_benchmark(summary_df, extras_df)

# ==============================
# Señales agregadas
# ==============================
signal_summary = _build_signal_summary(start_date, end_date)

# ==============================
# Lectura integrada
# ==============================
risk_level, risk_msg = _classify_risk(var_hist, persistencia, max_dd)
decision_title, decision_msg = _final_decision(
    risk_level=risk_level,
    signal_view=signal_summary["lectura"],
    bench_view=benchmark_level,
)

# ==============================
# Cabecera ejecutiva
# ==============================
st.subheader("Lectura ejecutiva")
st.caption(
    "La evaluación combina información estadística, técnica y de mercado para construir una visión integral del portafolio."
)

col1, col2, col3 = st.columns(3)
col1.metric("Riesgo", risk_level)
col2.metric("Señales", signal_summary["lectura"])
col3.metric("Benchmark", benchmark_level)

col4, col5, col6 = st.columns(3)
col4.metric("VaR histórico diario", f"{var_hist:.2%}" if pd.notna(var_hist) else "N/D")
col5.metric("CVaR histórico diario", f"{cvar_hist:.2%}" if pd.notna(cvar_hist) else "N/D")
col6.metric("Persistencia GARCH", f"{persistencia:.3f}" if pd.notna(persistencia) else "N/D")

st.markdown("---")

st.subheader("Lectura estratégica del portafolio")
st.markdown(f"### {decision_title}")
st.write(
    f"""
    {decision_msg}

    Esta conclusión se basa en la integración de métricas de riesgo extremo (VaR/CVaR),
    dinámica de volatilidad (GARCH), señales técnicas agregadas y desempeño relativo
    frente al benchmark de mercado.

    La lectura no debe interpretarse como una recomendación aislada, sino como una
    evaluación conjunta del perfil riesgo-retorno del portafolio en el contexto actual.
    """
)

# ==============================
# Comentarios integrados
# ==============================
st.subheader("Resumen integrado")

st.write(f"**Riesgo:** {risk_msg}")
st.write(f"**Benchmark:** {benchmark_msg}")

if garch_results.get("summary_text"):
    st.write(f"**Volatilidad condicional:** {garch_results['summary_text']}")
else:
    st.write("**Volatilidad condicional:** No fue posible generar una lectura GARCH robusta para esta ventana.")

if signal_summary["lectura"] == "Sesgo técnico favorable":
    st.write("**Señales técnicas:** Predominan señales de fortaleza o entrada táctica.")
elif signal_summary["lectura"] == "Sesgo técnico desfavorable":
    st.write("**Señales técnicas:** Predominan señales de deterioro técnico o cautela.")
else:
    st.write("**Señales técnicas:** La lectura agregada es mixta o neutral.")

# ==============================
# Detalle compacto
# ==============================
with st.expander("Ver detalle de benchmark"):
    if summary_df.empty:
        st.info("No hay comparación disponible frente al benchmark.")
    else:
        st.dataframe(summary_df, width="stretch")
        st.dataframe(extras_df, width="stretch")

with st.expander("Ver detalle de riesgo extremo"):
    st.dataframe(risk_table, width="stretch")

with st.expander("Ver detalle de señales por activo"):
    if signal_summary["detalle"].empty:
        st.info("No hay detalle de señales disponible.")
    else:
        st.dataframe(signal_summary["detalle"], width="stretch", hide_index=True)

with st.expander("Ver diagnóstico GARCH del portafolio"):
    if garch_results["comparison"].empty:
        st.info("No fue posible ajustar GARCH con calidad suficiente para esta ventana.")
    else:
        st.dataframe(garch_results["comparison"], width="stretch")
        st.dataframe(garch_results["diagnostics"], width="stretch")