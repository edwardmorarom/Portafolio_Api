from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import (
    header_dashboard,
    seccion,
    nota,
    tarjeta_kpi,
    plot_card_footer,
)

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import load_market_bundle, download_single_ticker
from src.preprocess import equal_weight_portfolio
from src.risk_metrics import risk_comparison_table, validar_serie_para_garch
from src.garch_models import fit_garch_models
from src.benchmark import benchmark_summary
from src.indicators import compute_all_indicators
from src.signals import evaluate_signals

try:
    from src.api.macro import macro_snapshot
except Exception:
    macro_snapshot = None

ensure_project_dirs()


# ==============================
# ESTILOS LOCALES
# ==============================
st.markdown(
    """
    <style>
    .decision-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.7rem;
        margin-top: 0.4rem;
        margin-bottom: 1.1rem;
    }

    .decision-mini-meta {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 0.85rem;
        border-radius: 999px;
        background: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.30);
        font-size: 0.83rem;
        font-weight: 700;
        color: #334155 !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    .decision-mini-meta strong,
    .decision-mini-meta span,
    .decision-mini-meta div {
        color: #334155 !important;
    }

    .decision-hero {
        border-radius: 24px;
        padding: 1.3rem 1.35rem;
        border: 1px solid rgba(148, 163, 184, 0.22);
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        margin-bottom: 1rem;
    }

    .decision-hero.positive {
        background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%);
        border-color: rgba(22, 163, 74, 0.22);
    }

    .decision-hero.warning {
        background: linear-gradient(135deg, #FFFBEA 0%, #FEFCE8 100%);
        border-color: rgba(234, 179, 8, 0.24);
    }

    .decision-hero.danger {
        background: linear-gradient(135deg, #FFF1F2 0%, #FEF2F2 100%);
        border-color: rgba(220, 38, 38, 0.22);
    }

    .decision-hero.neutral {
        background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 100%);
        border-color: rgba(100, 116, 139, 0.20);
    }

    .decision-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.42rem 0.78rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
        margin-bottom: 0.8rem;
        background: rgba(255,255,255,0.72);
        color: #334155;
        border: 1px solid rgba(148, 163, 184, 0.18);
    }

    .decision-title {
        font-size: 1.75rem;
        line-height: 1.1;
        font-weight: 800;
        color: #0F172A !important;
        margin-bottom: 0.55rem;
    }

    .decision-subtitle {
        font-size: 0.96rem;
        line-height: 1.6;
        color: #334155 !important;
    }

    .decision-support-box {
        background: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 1rem 1rem;
        margin-top: 0.6rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }

    .decision-support-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #0F172A !important;
        margin-bottom: 0.35rem;
    }

    .decision-support-text {
        font-size: 0.9rem;
        color: #475569 !important;
        line-height: 1.6;
    }

    .decision-list-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: 18px;
        padding: 1rem 1rem;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        margin-top: 0.5rem;
    }

    .decision-list-title {
        font-size: 0.92rem;
        font-weight: 900;
        color: #0F172A !important;
        margin-bottom: 0.45rem;
    }

    .decision-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        background: #0F172A;
        color: #ffffff !important;
        font-size: 0.78rem;
        font-weight: 800;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }

    .decision-soft-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        background: #EFF6FF;
        color: #1D4ED8 !important;
        font-size: 0.78rem;
        font-weight: 800;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        border: 1px solid rgba(59, 130, 246, 0.18);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================
# HELPERS LÓGICOS
# ==============================
def _get_rf_annual() -> float:
    if macro_snapshot is not None:
        try:
            snap = macro_snapshot()
            return float(snap.get("risk_free_rate_pct", 3.0)) / 100.0
        except Exception:
            return 0.03
    return 0.03


def _safe_float(x, default=np.nan):
    try:
        return float(x)
    except Exception:
        return default


def _get_profile_config(profile_name: str) -> dict:
    profiles = {
        "Conservador": {
            "label": "Conservador",
            "desc": (
                "Prioriza preservación de capital. Penaliza más el VaR, la persistencia GARCH "
                "y el drawdown. La decisión final exige mayor evidencia para comprar."
            ),
            "decision_weights": {"riesgo": 0.50, "tecnica": 0.20, "benchmark": 0.30},
            "risk_thresholds": {"var_high": 0.020, "var_mid": 0.010, "pers_high": 0.95, "pers_mid": 0.88, "dd_high": 0.18, "dd_mid": 0.08},
            "buy_threshold": 0.35,
            "hold_threshold": 0.00,
        },
        "Balanceado": {
            "label": "Balanceado",
            "desc": (
                "Busca equilibrio entre retorno y control de riesgo. Mantiene una lectura intermedia "
                "entre prudencia y oportunidad táctica."
            ),
            "decision_weights": {"riesgo": 0.40, "tecnica": 0.30, "benchmark": 0.30},
            "risk_thresholds": {"var_high": 0.030, "var_mid": 0.015, "pers_high": 0.98, "pers_mid": 0.90, "dd_high": 0.25, "dd_mid": 0.10},
            "buy_threshold": 0.25,
            "hold_threshold": -0.10,
        },
        "Agresivo": {
            "label": "Agresivo",
            "desc": (
                "Tolera mayor volatilidad para capturar oportunidades. Da más peso a la lectura técnica "
                "y al desempeño relativo, y acepta un riesgo más alto antes de castigar la decisión."
            ),
            "decision_weights": {"riesgo": 0.25, "tecnica": 0.45, "benchmark": 0.30},
            "risk_thresholds": {"var_high": 0.040, "var_mid": 0.020, "pers_high": 0.99, "pers_mid": 0.92, "dd_high": 0.30, "dd_mid": 0.12},
            "buy_threshold": 0.15,
            "hold_threshold": -0.15,
        },
    }
    return profiles.get(profile_name, profiles["Balanceado"])


def _signal_bucket(recommendation: str) -> str:
    txt = str(recommendation).lower()
    if "compra" in txt:
        return "favorable"
    if "venta" in txt:
        return "desfavorable"
    return "neutral"


def _build_signal_summary(start_date, end_date, selected_tickers: list[str]) -> dict:
    favorables = 0
    neutrales = 0
    desfavorables = 0

    favorables_tickers = []
    neutrales_tickers = []
    desfavorables_tickers = []

    for ticker in selected_tickers:
        try:
            df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))
            if df.empty:
                continue

            ind = compute_all_indicators(df)
            signal = evaluate_signals(ind)
            if not signal:
                continue

            recommendation = str(signal.get("recommendation", ""))
            bucket = _signal_bucket(recommendation)

            if bucket == "favorable":
                favorables += 1
                favorables_tickers.append(ticker)
            elif bucket == "desfavorable":
                desfavorables += 1
                desfavorables_tickers.append(ticker)
            else:
                neutrales += 1
                neutrales_tickers.append(ticker)
        except Exception:
            continue

    if favorables > desfavorables:
        lectura = "Favorable"
        score = 1
        ui = "positive"
    elif desfavorables > favorables:
        lectura = "Desfavorable"
        score = -1
        ui = "danger"
    else:
        lectura = "Neutral"
        score = 0
        ui = "warning"

    return {
        "lectura": lectura,
        "score": score,
        "ui": ui,
        "favorables": favorables,
        "neutrales": neutrales,
        "desfavorables": desfavorables,
        "favorables_tickers": favorables_tickers,
        "neutrales_tickers": neutrales_tickers,
        "desfavorables_tickers": desfavorables_tickers,
    }


def _classify_risk(var_hist: float, persistencia: float, max_dd: float, profile_cfg: dict) -> dict:
    dd_abs = abs(max_dd) if pd.notna(max_dd) else np.nan
    puntos = 0
    th = profile_cfg["risk_thresholds"]

    if pd.notna(var_hist):
        if var_hist >= th["var_high"]:
            puntos += 2
        elif var_hist >= th["var_mid"]:
            puntos += 1

    if pd.notna(persistencia):
        if persistencia >= th["pers_high"]:
            puntos += 2
        elif persistencia >= th["pers_mid"]:
            puntos += 1

    if pd.notna(dd_abs):
        if dd_abs >= th["dd_high"]:
            puntos += 2
        elif dd_abs >= th["dd_mid"]:
            puntos += 1

    if puntos >= 5:
        return {
            "nivel": "Alto",
            "score": -1,
            "ui": "danger",
            "mensaje": "El perfil de riesgo es elevado para el horizonte analizado y para el perfil del inversor seleccionado.",
        }
    if puntos >= 3:
        return {
            "nivel": "Medio",
            "score": 0,
            "ui": "warning",
            "mensaje": "El portafolio se ubica en una zona intermedia: no obliga a salir, pero sí exige control de exposición.",
        }
    return {
        "nivel": "Bajo",
        "score": 1,
        "ui": "positive",
        "mensaje": "El perfil de riesgo luce relativamente contenido para la ventana analizada y para este perfil de inversor.",
    }


def _classify_benchmark(summary_df: pd.DataFrame, extras_df: pd.DataFrame) -> dict:
    if summary_df.empty:
        return {
            "nivel": "No concluyente",
            "score": 0,
            "ui": "warning",
            "mensaje": "No fue posible construir una comparación robusta frente al benchmark.",
        }

    try:
        port_ret = float(summary_df.loc[summary_df["serie"] == "Portafolio", "ret_anualizado"].iloc[0])
        bench_ret = float(summary_df.loc[summary_df["serie"] == "Benchmark", "ret_anualizado"].iloc[0])

        alpha = np.nan
        if not extras_df.empty and "Alpha de Jensen" in extras_df["métrica"].values:
            alpha = float(extras_df.loc[extras_df["métrica"] == "Alpha de Jensen", "valor"].iloc[0])

        if port_ret > bench_ret and (pd.isna(alpha) or alpha >= 0):
            return {
                "nivel": "Superior",
                "score": 1,
                "ui": "positive",
                "mensaje": "El portafolio presenta una lectura relativa favorable frente al benchmark.",
            }

        if port_ret < bench_ret and (pd.isna(alpha) or alpha < 0):
            return {
                "nivel": "Inferior",
                "score": -1,
                "ui": "danger",
                "mensaje": "El portafolio viene rezagado frente al benchmark y no muestra ventaja relativa consistente.",
            }

        return {
            "nivel": "No concluyente",
            "score": 0,
            "ui": "warning",
            "mensaje": "La comparación relativa es mixta y no confirma dominancia clara.",
        }
    except Exception:
        return {
            "nivel": "No concluyente",
            "score": 0,
            "ui": "warning",
            "mensaje": "No fue posible construir una lectura comparativa suficientemente robusta.",
        }


def _weighted_final_decision(risk_score: int, signal_score: int, bench_score: int, decision_weights: dict, profile_cfg: dict) -> dict:
    total = (
        risk_score * decision_weights["riesgo"]
        + signal_score * decision_weights["tecnica"]
        + bench_score * decision_weights["benchmark"]
    )

    buy_threshold = profile_cfg["buy_threshold"]
    hold_threshold = profile_cfg["hold_threshold"]

    if total >= buy_threshold:
        return {
            "titulo": "Compra táctica",
            "ui": "positive",
            "mensaje_general": "La lectura integrada favorece una postura compradora o de incremento táctico de exposición.",
            "mensaje_riesgo": "El principal riesgo es que un cambio brusco de mercado revierta la señal técnica y deteriore el perfil de volatilidad.",
            "mensaje_formal": "La combinación ponderada entre riesgo, señales y benchmark respalda una postura de compra táctica para el perfil seleccionado.",
            "score_total": total,
        }

    if total >= hold_threshold:
        return {
            "titulo": "Mantener / compra selectiva",
            "ui": "warning",
            "mensaje_general": "La lectura integrada permite mantener exposición y considerar compras selectivas, pero no justifica una expansión agresiva de riesgo.",
            "mensaje_riesgo": "El principal riesgo es entrar con confirmación incompleta y enfrentar un deterioro posterior en benchmark o volatilidad.",
            "mensaje_formal": "La evidencia agregada no es lo bastante fuerte para una postura agresiva, pero tampoco justifica deshacer exposición. La decisión razonable es mantener y comprar de forma selectiva.",
            "score_total": total,
        }

    if total >= -0.45:
        return {
            "titulo": "Reducir exposición",
            "ui": "warning",
            "mensaje_general": "La lectura integrada sugiere reducir parcialmente exposición o evitar nuevas compras hasta que mejoren las condiciones.",
            "mensaje_riesgo": "El riesgo central es mantener una posición relativamente alta en un contexto donde la evidencia agregada se ha debilitado.",
            "mensaje_formal": "La combinación de señales no favorece una ampliación de posición. La decisión más consistente es reducir exposición marginalmente y esperar mejor confirmación.",
            "score_total": total,
        }

    return {
        "titulo": "Venta / postura defensiva",
        "ui": "danger",
        "mensaje_general": "La lectura integrada favorece una postura defensiva: reducir exposición de forma relevante o priorizar salida.",
        "mensaje_riesgo": "El principal riesgo es permanecer sobreexpuesto en un entorno donde coinciden riesgo elevado, deterioro técnico y/o rezago relativo.",
        "mensaje_formal": "La evidencia integrada es adversa. Desde una perspectiva de control de riesgo, la postura más defendible es de venta o reducción sustancial de exposición.",
        "score_total": total,
    }


def _build_portfolio_returns(returns_df: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    clean_weights = np.asarray(weights, dtype=float)
    clean_weights = clean_weights / clean_weights.sum()
    return (returns_df * clean_weights).sum(axis=1)


def _render_chip_list(items: list[str], empty_text: str, soft: bool = False):
    if not items:
        st.info(empty_text)
        return

    chip_class = "decision-soft-chip" if soft else "decision-chip"
    html = "".join([f'<span class="{chip_class}">{x}</span>' for x in items])
    st.markdown(html, unsafe_allow_html=True)


def render_decision_hero(title: str, subtitle: str, level: str = "neutral"):
    st.markdown(
        f"""
        <div class="decision-hero {level}">
            <div class="decision-badge">Decisión integrada del portafolio</div>
            <div class="decision-title">{title}</div>
            <div class="decision-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros De Decisión",
    filtros_expanded=False,
)

all_tickers = [meta["ticker"] for meta in ASSETS.values()]


# ==============================
# SIDEBAR
# ==============================
with filtros_sidebar:
    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="decision_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="decision_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="decision_end")

    selected_tickers = st.multiselect(
        "Selecciona activos",
        options=all_tickers,
        default=all_tickers,
        key="decision_selected_tickers",
        help="Escoge los activos que quieres incluir en el panel de decisión.",
    )

    investor_profile = st.selectbox(
        "Perfil del inversor",
        ["Conservador", "Balanceado", "Agresivo", "Personalizado"],
        index=1,
        key="decision_profile",
        help=(
            "Conservador: penaliza más el riesgo y exige más evidencia para comprar.\n\n"
            "Balanceado: combina riesgo, señales y benchmark con pesos intermedios.\n\n"
            "Agresivo: tolera más volatilidad y da mayor peso a señales y benchmark.\n\n"
            "Personalizado: tú defines manualmente la importancia de riesgo, técnica y benchmark."
        ),
    )

    portfolio_mode = st.radio(
        "Construcción del portafolio",
        ["Equiponderado", "Pesos manuales"],
        index=0,
        key="decision_portfolio_mode",
        help="Equiponderado asigna el mismo peso a todos los activos. Pesos manuales permite definir la asignación del inversor.",
    )

    mostrar_detalle = st.checkbox(
        "Mostrar detalle técnico",
        value=(modo == "Estadístico"),
        key="decision_show_detail",
    )

    with st.expander("Filtros secundarios", expanded=False):
        alpha = st.select_slider(
            "Nivel de confianza VaR",
            options=[0.95, 0.96, 0.97, 0.98, 0.99],
            value=0.95,
            key="decision_alpha",
        )
        n_sim = st.slider(
            "Simulaciones Monte Carlo",
            min_value=5000,
            max_value=50000,
            value=10000,
            step=5000,
            key="decision_nsim",
        )

    # Pesos del portafolio
    manual_weights_pct = {}
    if portfolio_mode == "Pesos manuales":
        st.markdown("**Pesos del portafolio (%)**")
        for ticker in selected_tickers:
            manual_weights_pct[ticker] = st.number_input(
                f"Peso {ticker}",
                min_value=0.0,
                max_value=100.0,
                value=round(100.0 / max(len(selected_tickers), 1), 2),
                step=1.0,
                key=f"weight_{ticker}",
            )

        total_manual_weights = sum(manual_weights_pct.values())
        if abs(total_manual_weights - 100.0) > 0.01:
            st.error(f"La suma de los pesos debe ser 100%. Actualmente suma {total_manual_weights:.2f}%.")
        else:
            st.success("La suma de pesos es válida: 100%.")

    # Pesos de decisión
    if investor_profile == "Personalizado":
        st.markdown("**Importancia de cada bloque (%)**")
        risk_pct = st.slider("Riesgo", 0, 100, 40, 5, key="decision_w_risk")
        tech_pct = st.slider("Técnica", 0, 100, 30, 5, key="decision_w_tech")
        bench_pct = st.slider("Benchmark", 0, 100, 30, 5, key="decision_w_bench")

        total_decision_pct = risk_pct + tech_pct + bench_pct
        if total_decision_pct != 100:
            st.warning(f"La suma actual es {total_decision_pct}%. Debe ser 100%.")
        else:
            st.success("La suma de pesos de decisión es 100%.")

        profile_cfg = {
            "label": "Personalizado",
            "desc": (
                "El usuario define manualmente cuánto pesa el riesgo, la lectura técnica y el benchmark "
                "en la decisión final del portafolio."
            ),
            "decision_weights": {
                "riesgo": risk_pct / 100.0,
                "tecnica": tech_pct / 100.0,
                "benchmark": bench_pct / 100.0,
            },
            "risk_thresholds": {"var_high": 0.030, "var_mid": 0.015, "pers_high": 0.98, "pers_mid": 0.90, "dd_high": 0.25, "dd_mid": 0.10},
            "buy_threshold": 0.25,
            "hold_threshold": -0.10,
        }
    else:
        profile_cfg = _get_profile_config(investor_profile)


# ==============================
# VALIDACIONES
# ==============================
if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

if not selected_tickers:
    st.warning("Selecciona al menos un activo para continuar.")
    st.stop()

if portfolio_mode == "Pesos manuales":
    total_manual_weights = sum(manual_weights_pct.values())
    if abs(total_manual_weights - 100.0) > 0.01:
        st.stop()

if investor_profile == "Personalizado":
    if (risk_pct + tech_pct + bench_pct) != 100:
        st.stop()


# ==============================
# DATOS BASE
# ==============================
bundle = load_market_bundle(tickers=selected_tickers, start=str(start_date), end=str(end_date))
returns = bundle["returns"].replace([np.inf, -np.inf], np.nan).dropna()

if returns.empty or len(returns) < 30:
    st.error("No hay suficientes datos para construir el panel de decisión.")
    st.stop()

if portfolio_mode == "Equiponderado":
    weights = np.repeat(1.0 / returns.shape[1], returns.shape[1])
else:
    weights = np.array([manual_weights_pct[t] / 100.0 for t in returns.columns], dtype=float)

portfolio_returns = _build_portfolio_returns(returns, weights)
rf_annual = _get_rf_annual()

# Riesgo extremo
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
    var_hist = _safe_float(row_hist["VaR_diario"])
    cvar_hist = _safe_float(row_hist["CVaR_diario"])

# GARCH
garch_validation = validar_serie_para_garch(portfolio_returns, min_obs=120, max_null_ratio=0.05)
persistencia = np.nan

if garch_validation["ok"]:
    serie_garch = garch_validation["serie_limpia"] * 100.0
    garch_results = fit_garch_models(serie_garch)
else:
    garch_results = {"comparison": pd.DataFrame(), "diagnostics": pd.DataFrame(), "summary_text": ""}

if not garch_results["diagnostics"].empty:
    persist_row = garch_results["diagnostics"].loc[
        garch_results["diagnostics"]["metrica"] == "persistencia_alpha_mas_beta"
    ]
    if not persist_row.empty:
        persistencia = pd.to_numeric(persist_row["valor"], errors="coerce").iloc[0]

# Benchmark
summary_df = pd.DataFrame()
extras_df = pd.DataFrame()
max_dd = np.nan

try:
    bench_df = yf.download("^GSPC", start=str(start_date), end=str(end_date), auto_adjust=False)

    if not bench_df.empty:
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

        if not benchmark_returns.empty:
            summary_df, extras_df, _, _ = benchmark_summary(
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
                rf_annual=rf_annual,
            )
except Exception:
    summary_df = pd.DataFrame()
    extras_df = pd.DataFrame()

if not summary_df.empty:
    try:
        max_dd = float(summary_df.loc[summary_df["serie"] == "Portafolio", "max_drawdown"].iloc[0])
    except Exception:
        max_dd = np.nan

# Señales
signal_summary = _build_signal_summary(start_date, end_date, selected_tickers)

# Clasificaciones
risk_view = _classify_risk(var_hist, persistencia, max_dd, profile_cfg)
bench_view = _classify_benchmark(summary_df, extras_df)
decision = _weighted_final_decision(
    risk_view["score"],
    signal_summary["score"],
    bench_view["score"],
    profile_cfg["decision_weights"],
    profile_cfg,
)


# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 9 - Panel de decisión",
    "Integra riesgo, volatilidad, señales técnicas, benchmark y preferencias del inversor para producir una postura de acción más ajustada al usuario.",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo resume la evidencia más importante del portafolio y la adapta al perfil del inversor para convertirla en una postura concreta de acción."
    )
else:
    nota(
        "La decisión se construye con una agregación ponderada entre riesgo, señales técnicas y benchmark, ajustada por el perfil o por los pesos personalizados del usuario."
    )


# ==============================
# RESUMEN DEL MÓDULO
# ==============================
seccion("Resumen Del Módulo")

st.markdown(
    f"""
    <div class="decision-meta-row">
        <div class="decision-mini-meta"><strong>Horizonte:</strong>&nbsp;{horizonte}</div>
        <div class="decision-mini-meta"><strong>Inicio:</strong>&nbsp;{start_date}</div>
        <div class="decision-mini-meta"><strong>Fin:</strong>&nbsp;{end_date}</div>
        <div class="decision-mini-meta"><strong>VaR:</strong>&nbsp;{int(alpha * 100)}%</div>
        <div class="decision-mini-meta"><strong>Monte Carlo:</strong>&nbsp;{n_sim:,}</div>
        <div class="decision-mini-meta"><strong>Perfil:</strong>&nbsp;{profile_cfg["label"]}</div>
        <div class="decision-mini-meta"><strong>Portafolio:</strong>&nbsp;{portfolio_mode}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_text = decision["mensaje_general"] if modo == "General" else decision["mensaje_formal"]
render_decision_hero(decision["titulo"], hero_text, level=decision["ui"])

seccion("Perfil Del Inversor Aplicado")
nota(profile_cfg["desc"])
nota(
    f"Peso de decisión aplicado → Riesgo: {profile_cfg['decision_weights']['riesgo']:.0%} | "
    f"Técnica: {profile_cfg['decision_weights']['tecnica']:.0%} | "
    f"Benchmark: {profile_cfg['decision_weights']['benchmark']:.0%}"
)


# ==============================
# TABS
# ==============================
tab1, tab2, tab3 = st.tabs(
    [
        "Decisión integrada",
        "Métricas de soporte",
        "Detalle técnico",
    ]
)


# ==============================
# TAB 1
# ==============================
with tab1:
    seccion("Pilares De La Decisión")

    p1, p2, p3 = st.columns(3)

    with p1:
        tarjeta_kpi(
            "Riesgo",
            risk_view["nivel"],
            help_text="Clasificación agregada del perfil de riesgo a partir de VaR histórico, persistencia GARCH y drawdown.",
            subtexto=risk_view["mensaje"],
        )

    with p2:
        tarjeta_kpi(
            "Lectura técnica",
            signal_summary["lectura"],
            help_text="Se resume con base en el balance entre señales favorables, neutrales y desfavorables del conjunto de activos.",
            subtexto=(
                f"Favorables: {signal_summary['favorables']} | "
                f"Neutrales: {signal_summary['neutrales']} | "
                f"Desfavorables: {signal_summary['desfavorables']}"
            ),
        )

    with p3:
        tarjeta_kpi(
            "Benchmark",
            bench_view["nivel"],
            help_text="Compara el desempeño relativo del portafolio frente al benchmark usando retorno anualizado y alpha de Jensen.",
            subtexto=bench_view["mensaje"],
        )

    plot_card_footer(
        f"Decisión sugerida: {decision['titulo']}. "
        f"El panel consolida la evidencia de riesgo, técnica y benchmark y la ajusta al perfil del inversor."
    )

    seccion("Interpretación De La Postura")

    if modo == "General":
        nota(
            f"La decisión actual del panel es {decision['titulo']}. Esto significa que, bajo la evidencia observada y el perfil {profile_cfg['label'].lower()}, la combinación de riesgo, señales y benchmark favorece la siguiente lectura: {decision['mensaje_general']}"
        )
        nota(
            f"El principal riesgo de implementación es el siguiente: {decision['mensaje_riesgo']}"
        )
    else:
        nota(
            f"La clasificación final del panel es {decision['titulo']}. No debe entenderse como una predicción puntual, sino como una postura razonable dada la información consolidada y las preferencias del usuario."
        )
        nota(
            f"Conclusión formal: {decision['mensaje_formal']}"
        )
        nota(
            f"Riesgo de implementación: {decision['mensaje_riesgo']}"
        )

    seccion("Compras Selectivas Recomendadas")

    if decision["titulo"] in ["Compra táctica", "Mantener / compra selectiva"]:
        if signal_summary["favorables_tickers"]:
            st.markdown(
                """
                <div class="decision-list-card">
                    <div class="decision-list-title">Activos con lectura favorable</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            _render_chip_list(
                signal_summary["favorables_tickers"],
                "No hay activos con señal favorable clara en esta ventana.",
            )

            nota(
                "Estas compras selectivas corresponden a los activos que presentan lectura técnica favorable dentro del universo analizado. No implica comprar todos los activos del portafolio, sino priorizar aquellos con mejor confirmación relativa."
            )
        else:
            st.info("No se recomiendan compras selectivas en esta ventana: no hay activos con señal favorable suficientemente clara.")
    else:
        st.info("La postura actual no favorece nuevas compras; primero debería mejorar la evidencia agregada del panel.")


# ==============================
# TAB 2
# ==============================
with tab2:
    seccion("Indicadores Clave De Soporte")

    alpha_jensen = np.nan
    if not extras_df.empty and "Alpha de Jensen" in extras_df["métrica"].values:
        try:
            alpha_jensen = float(extras_df.loc[extras_df["métrica"] == "Alpha de Jensen", "valor"].iloc[0])
        except Exception:
            alpha_jensen = np.nan

    balance_signals = signal_summary["favorables"] - signal_summary["desfavorables"]

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        tarjeta_kpi(
            "VaR histórico",
            f"{var_hist:.2%}" if pd.notna(var_hist) else "N/D",
            help_text="Pérdida umbral estimada del portafolio bajo la distribución histórica observada.",
            subtexto="Sirve como aproximación de pérdida potencial diaria.",
        )

    with k2:
        tarjeta_kpi(
            "Persistencia GARCH",
            f"{persistencia:.3f}" if pd.notna(persistencia) else "N/D",
            help_text="Mide la memoria de la volatilidad en el portafolio.",
            subtexto="Valores altos sugieren que los choques de volatilidad tardan más en disiparse.",
        )

    with k3:
        tarjeta_kpi(
            "Alpha de Jensen",
            f"{alpha_jensen:.4f}" if pd.notna(alpha_jensen) else "N/D",
            help_text="Exceso de desempeño ajustado por riesgo sistemático frente al benchmark.",
            subtexto="Ayuda a validar si el portafolio realmente agregó valor relativo.",
        )

    with k4:
        tarjeta_kpi(
            "Balance de señales",
            str(balance_signals),
            help_text="Diferencia entre señales favorables y desfavorables del conjunto de activos.",
            subtexto="Un valor positivo sugiere sesgo comprador; uno negativo, sesgo vendedor.",
        )

    if pd.notna(cvar_hist):
        c1, c2 = st.columns(2)
        with c1:
            tarjeta_kpi(
                "CVaR histórico",
                f"{cvar_hist:.2%}",
                help_text="Pérdida media esperada una vez se supera el umbral VaR.",
                subtexto="Complementa al VaR al medir severidad de pérdidas extremas.",
            )
        with c2:
            tarjeta_kpi(
                "Tasa libre de riesgo",
                f"{rf_annual:.2%}",
                help_text="Se obtiene del módulo macroeconómico y se usa en métricas ajustadas por riesgo.",
                subtexto="Si no hay dato disponible, el sistema usa un fallback de 3% anual.",
            )

    seccion("Asignación Del Portafolio")

    weights_df = pd.DataFrame(
        {
            "Ticker": list(returns.columns),
            "Peso": [f"{w:.2%}" for w in weights],
        }
    )
    st.dataframe(weights_df, use_container_width=True, hide_index=True)

    plot_card_footer(
        "Estas métricas no reemplazan el juicio de inversión, pero sí justifican la decisión integrada que emite el panel."
    )


# ==============================
# TAB 3
# ==============================
with tab3:
    seccion("Detalle Técnico Del Score")

    detalle_df = pd.DataFrame(
        {
            "Componente": ["Riesgo", "Técnica", "Benchmark", "Score ponderado total"],
            "Lectura": [
                risk_view["nivel"],
                signal_summary["lectura"],
                bench_view["nivel"],
                f"{decision['score_total']:.3f}",
            ],
            "Score base": [
                risk_view["score"],
                signal_summary["score"],
                bench_view["score"],
                "",
            ],
            "Peso aplicado": [
                f"{profile_cfg['decision_weights']['riesgo']:.0%}",
                f"{profile_cfg['decision_weights']['tecnica']:.0%}",
                f"{profile_cfg['decision_weights']['benchmark']:.0%}",
                "",
            ],
        }
    )
    st.dataframe(detalle_df, use_container_width=True, hide_index=True)

    seccion("Detalle De Señales Por Grupo")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="decision-list-card">
                <div class="decision-list-title">Favorables</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_chip_list(signal_summary["favorables_tickers"], "No hay activos favorables.")

    with c2:
        st.markdown(
            """
            <div class="decision-list-card">
                <div class="decision-list-title">Neutrales</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_chip_list(signal_summary["neutrales_tickers"], "No hay activos neutrales.", soft=True)

    with c3:
        st.markdown(
            """
            <div class="decision-list-card">
                <div class="decision-list-title">Desfavorables</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_chip_list(signal_summary["desfavorables_tickers"], "No hay activos desfavorables.", soft=True)

    if mostrar_detalle:
        seccion("Tablas Complementarias")

        c1, c2 = st.columns(2)

        with c1:
            with st.expander("Ver tabla de riesgo extremo", expanded=False):
                st.dataframe(risk_table, use_container_width=True, hide_index=True)

        with c2:
            with st.expander("Ver comparación frente al benchmark", expanded=False):
                if not summary_df.empty:
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No fue posible construir la tabla comparativa del benchmark.")

        with st.expander("Ver métricas adicionales del benchmark", expanded=False):
            if not extras_df.empty:
                st.dataframe(extras_df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay métricas adicionales disponibles.")

        with st.expander("Ver diagnósticos GARCH", expanded=False):
            if "diagnostics" in garch_results and not garch_results["diagnostics"].empty:
                st.dataframe(garch_results["diagnostics"], use_container_width=True, hide_index=True)
            else:
                st.info("No hay diagnósticos GARCH disponibles para la serie analizada.")

    seccion("Lectura Final")

    if modo == "General":
        nota(
            "El panel no toma la decisión con base en una sola métrica. Combina riesgo, lectura técnica y benchmark, y ahora además incorpora el perfil del inversor y la construcción del portafolio."
        )
    else:
        nota(
            "La metodología implementa una regla de agregación ponderada entre tres dimensiones relevantes del portafolio. Su objetivo no es maximizar complejidad, sino producir una salida integrada, ajustable y justificable."
        )