from __future__ import annotations

from typing import Any, Optional

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
    plot_card_header,
    plot_card_footer,
    toolbar_label,
)

from src.config import (
    ASSETS,
    GLOBAL_BENCHMARK,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    ensure_project_dirs,
)
from src.download import load_market_bundle, download_single_ticker
from src.indicators import compute_all_indicators
from src.signals import evaluate_signals
from src.garch_models import fit_garch_models
from src.risk_metrics import risk_comparison_table, validar_serie_para_garch
from src.benchmark import benchmark_summary
from src.plots import plot_benchmark_base100
from src.decision_engine import (
    DecisionEngineInputs,
    EngineDependencies,
    build_portfolio_weights,
    run_decision_engine,
)

try:
    from src.api.macro import macro_snapshot
except Exception:
    macro_snapshot = None

ensure_project_dirs()


# ==============================
# HELPERS VISUALES
# ==============================
def style_plot(fig, modo: str):
    font_color = "#5B2132" if modo == "Estadístico" else "#334155"
    grid_color = "rgba(148, 163, 184, 0.16)"
    axis_title = "#0F172A"
    tick_color = "#334155"
    legend_font = "#334155" if modo == "General" else "#5B2132"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color, size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="rgba(148, 163, 184, 0.22)",
            borderwidth=1,
            font=dict(color=legend_font, size=11),
        ),
        margin=dict(l=20, r=20, t=70, b=20),
        hoverlabel=dict(
            font_size=12,
            bgcolor="#FFFFFF",
            font_color="#0F172A",
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(color=tick_color, size=12),
        title_font=dict(color=axis_title, size=14, family="Inter, sans-serif"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(color=tick_color, size=12),
        title_font=dict(color=axis_title, size=14, family="Inter, sans-serif"),
    )
    return fig


def safe_metric(df: pd.DataFrame, filter_col: str, filter_val: str, value_col: str) -> Optional[float]:
    try:
        return float(df.loc[df[filter_col] == filter_val, value_col].iloc[0])
    except Exception:
        return None


def delta_label(value, positive_text, negative_text, neutral_text="Sin cambio"):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if value > 0:
        return positive_text
    if value < 0:
        return negative_text
    return neutral_text


def interpret_macro_context(rf_pct, inflation_yoy, usdcop_market, cop_per_usd):
    parts = []

    if rf_pct is not None:
        parts.append(f"la tasa libre de riesgo se ubica en {rf_pct:.2f}%")

    if inflation_yoy is not None:
        parts.append(f"la inflación interanual se estima en {inflation_yoy:.2%}")

    if usdcop_market is not None and cop_per_usd is not None:
        if usdcop_market > cop_per_usd:
            parts.append("el USD/COP spot se encuentra por encima de su promedio anual")
        elif usdcop_market < cop_per_usd:
            parts.append("el USD/COP spot se encuentra por debajo de su promedio anual")
        else:
            parts.append("el USD/COP spot es similar a su promedio anual")

    if not parts:
        return "No fue posible construir una lectura automática del contexto macro."
    return "En el periodo analizado, " + ", ".join(parts) + "."


def interpret_relative_performance(ret_port, ret_bench, alpha_jensen, tracking_error):
    parts = []

    if ret_port is not None and ret_bench is not None:
        diff_ret = ret_port - ret_bench
        if diff_ret > 0:
            parts.append(f"el portafolio superó al benchmark por {diff_ret:.2%}")
        elif diff_ret < 0:
            parts.append(f"el portafolio quedó por debajo del benchmark en {abs(diff_ret):.2%}")
        else:
            parts.append("el portafolio tuvo un desempeño acumulado similar al benchmark")

    if alpha_jensen is not None:
        if alpha_jensen > 0:
            parts.append("el alpha de Jensen fue positivo")
        elif alpha_jensen < 0:
            parts.append("el alpha de Jensen fue negativo")
        else:
            parts.append("el alpha de Jensen fue cercano a cero")

    if tracking_error is not None:
        parts.append(f"el tracking error fue de {tracking_error:.4f}")

    if not parts:
        return "No fue posible construir una interpretación automática del desempeño relativo."
    return "En síntesis, " + ", ".join(parts) + "."


def benchmark_label(tone: str) -> str:
    mapping = {
        "positive": "Superior",
        "slightly_positive": "Levemente superior",
        "neutral": "No concluyente",
        "negative": "Inferior",
    }
    return mapping.get(str(tone), "No concluyente")


def signal_label(tone: str) -> str:
    mapping = {
        "strong_positive": "Favorable fuerte",
        "positive": "Favorable",
        "neutral": "Neutral",
        "negative": "Desfavorable",
        "strong_negative": "Desfavorable fuerte",
    }
    return mapping.get(str(tone), "Neutral")


def _weighting_label(construction_mode: str) -> str:
    mapping = {
        "equal": "Portafolio equiponderado",
        "manual": "Portafolio con pesos manuales",
        "min_variance": "Portafolio de mínima varianza",
        "max_utility": "Portafolio de máxima utilidad",
    }
    return mapping.get(construction_mode, "Construcción no especificada")


# ==============================
# HELPERS DE DATOS
# ==============================
def _extract_prices_from_bundle(bundle: dict, tickers: list[str]) -> pd.DataFrame:
    for key in ("prices", "adj_close", "close"):
        value = bundle.get(key)
        if isinstance(value, pd.DataFrame) and not value.empty:
            cols = [c for c in tickers if c in value.columns]
            if cols:
                return value[cols].copy()
    return pd.DataFrame()


def _get_macro() -> dict[str, Any]:
    if macro_snapshot is None:
        return {}
    try:
        snap = macro_snapshot()
        return snap if isinstance(snap, dict) else {}
    except Exception:
        return {}


def _get_rf_annual(macro: dict[str, Any]) -> float:
    try:
        rf_pct = macro.get("risk_free_rate_pct", np.nan)
        if pd.notna(rf_pct):
            return float(rf_pct) / 100.0
    except Exception:
        pass
    return 0.03


def _download_benchmark_returns(symbol: str, start_date, end_date) -> Optional[pd.Series]:
    try:
        bench_df = yf.download(
            symbol,
            start=str(start_date),
            end=str(end_date),
            auto_adjust=False,
            progress=False,
        )
        if bench_df.empty:
            return None

        if isinstance(bench_df.columns, pd.MultiIndex):
            if ("Adj Close", symbol) in bench_df.columns:
                prices = bench_df[("Adj Close", symbol)]
            elif ("Close", symbol) in bench_df.columns:
                prices = bench_df[("Close", symbol)]
            else:
                return None
        else:
            if "Adj Close" in bench_df.columns:
                prices = bench_df["Adj Close"]
            elif "Close" in bench_df.columns:
                prices = bench_df["Close"]
            else:
                return None

        prices = pd.to_numeric(prices, errors="coerce").dropna()
        returns = prices.pct_change().dropna()
        return returns if not returns.empty else None
    except Exception:
        return None


def _signal_bucket(recommendation: str) -> str:
    txt = str(recommendation).lower()
    if "compra" in txt:
        return "favorable"
    if "venta" in txt:
        return "desfavorable"
    return "neutral"


def _make_signal_adapter(start_date, end_date):
    def _adapter(_prices_df: pd.DataFrame, tickers: list[str]) -> dict[str, Any]:
        favorables: list[str] = []
        neutrales: list[str] = []
        desfavorables: list[str] = []
        rows: list[dict[str, Any]] = []

        for ticker in tickers:
            try:
                df = download_single_ticker(
                    ticker=ticker,
                    start=str(start_date),
                    end=str(end_date),
                )
                if df.empty:
                    rows.append(
                        {
                            "Ticker": ticker,
                            "Recomendación": "Sin datos",
                            "Bucket": "neutral",
                            "Detalle": "No hubo datos suficientes para evaluar señales.",
                        }
                    )
                    continue

                indicators_df = compute_all_indicators(df)
                signal = evaluate_signals(indicators_df) or {}
                recommendation = str(signal.get("recommendation", "Neutral"))
                bucket = _signal_bucket(recommendation)

                if bucket == "favorable":
                    favorables.append(ticker)
                elif bucket == "desfavorable":
                    desfavorables.append(ticker)
                else:
                    neutrales.append(ticker)

                rows.append(
                    {
                        "Ticker": ticker,
                        "Recomendación": recommendation,
                        "Bucket": bucket,
                        "Detalle": signal.get("message", ""),
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "Ticker": ticker,
                        "Recomendación": "No concluyente",
                        "Bucket": "neutral",
                        "Detalle": f"Falló la evaluación de señales: {exc}",
                    }
                )

        return {
            "favorables_tickers": favorables,
            "desfavorables_tickers": desfavorables,
            "neutrales_tickers": neutrales,
            "signal_table": pd.DataFrame(rows),
        }

    return _adapter


# ==============================
# OPTIMIZACIÓN DE PESOS
# ==============================
def _project_long_only(raw: np.ndarray, tickers: list[str]) -> pd.Series:
    s = pd.Series(raw, index=tickers, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    s = s.clip(lower=0.0)
    total = float(s.sum())
    if total <= 0:
        s = pd.Series(1.0 / len(tickers), index=tickers, dtype=float)
    else:
        s = s / total
    return s


def _solve_min_variance_weights(returns_df: pd.DataFrame, ridge: float = 1e-6) -> pd.Series:
    tickers = list(returns_df.columns)
    cov = returns_df.cov().to_numpy(dtype=float)
    n = cov.shape[0]
    cov_reg = cov + ridge * np.eye(n)
    inv_cov = np.linalg.pinv(cov_reg)
    ones = np.ones(n)
    raw = inv_cov @ ones
    return _project_long_only(raw, tickers)


def _solve_max_utility_weights(
    returns_df: pd.DataFrame,
    rf_annual: float,
    utility_focus: float = 0.65,
    ridge: float = 1e-6,
) -> pd.Series:
    tickers = list(returns_df.columns)
    mu = (returns_df.mean() * 252.0).to_numpy(dtype=float)
    cov = (returns_df.cov() * 252.0).to_numpy(dtype=float)
    n = cov.shape[0]

    cov_reg = cov + ridge * np.eye(n)
    inv_cov = np.linalg.pinv(cov_reg)
    ones = np.ones(n)

    min_var_raw = inv_cov @ ones
    utility_raw = inv_cov @ (mu - rf_annual)

    min_var_w = _project_long_only(min_var_raw, tickers)
    utility_w = _project_long_only(utility_raw, tickers)

    utility_focus = float(np.clip(utility_focus, 0.0, 1.0))
    blended = utility_focus * utility_w + (1.0 - utility_focus) * min_var_w
    blended = blended / blended.sum()
    return blended


def _resolve_portfolio_construction(
    selected_tickers: list[str],
    returns_df: pd.DataFrame,
    construction_choice: str,
    manual_weights_pct: dict[str, float],
    rf_annual: float,
    utility_focus: float,
) -> tuple[str, Optional[dict[str, float]], Optional[dict[str, float]], pd.Series]:
    if construction_choice == "Equiponderado":
        weights = build_portfolio_weights(
            tickers=selected_tickers,
            mode="equal",
        )
        return "equal", None, None, weights

    if construction_choice == "Pesos manuales":
        raw_sum = float(sum(manual_weights_pct.values()))
        manual_weights = {
            ticker: value / raw_sum
            for ticker, value in manual_weights_pct.items()
        }
        weights = build_portfolio_weights(
            tickers=selected_tickers,
            mode="manual",
            manual_weights=manual_weights,
        )
        return "manual", manual_weights, None, weights

    if construction_choice == "Mínima varianza":
        markowitz_series = _solve_min_variance_weights(returns_df[selected_tickers])
        markowitz_weights = markowitz_series.to_dict()
        weights = build_portfolio_weights(
            tickers=selected_tickers,
            mode="markowitz",
            markowitz_weights=markowitz_weights,
        )
        return "markowitz", None, markowitz_weights, weights

    markowitz_series = _solve_max_utility_weights(
        returns_df[selected_tickers],
        rf_annual=rf_annual,
        utility_focus=utility_focus,
    )
    markowitz_weights = markowitz_series.to_dict()
    weights = build_portfolio_weights(
        tickers=selected_tickers,
        mode="markowitz",
        markowitz_weights=markowitz_weights,
    )
    return "markowitz", None, markowitz_weights, weights


# ==============================
# ADAPTADORES DEL MOTOR
# ==============================
def _make_var_cvar_adapter(asset_returns_df: pd.DataFrame, weights: pd.Series, n_sim: int):
    def _adapter(portfolio_returns: pd.Series, confidence_level: float) -> dict[str, Any]:
        if asset_returns_df.empty:
            return {
                "var": np.nan,
                "cvar": np.nan,
                "method": "historical",
                "confidence_level": confidence_level,
                "comparison_table": pd.DataFrame(),
            }

        table = risk_comparison_table(
            portfolio_returns=portfolio_returns,
            asset_returns_df=asset_returns_df,
            weights=weights.values,
            alpha=confidence_level,
            n_sim=n_sim,
        )

        if table.empty or "Histórico" not in table["método"].values:
            return {
                "var": np.nan,
                "cvar": np.nan,
                "method": "historical",
                "confidence_level": confidence_level,
                "comparison_table": table,
            }

        row_hist = table.loc[table["método"] == "Histórico"].iloc[0]
        return {
            "var": float(row_hist["VaR_diario"]),
            "cvar": float(row_hist["CVaR_diario"]),
            "method": "historical_module",
            "confidence_level": confidence_level,
            "comparison_table": table,
        }

    return _adapter


def _garch_adapter(portfolio_returns: pd.Series) -> dict[str, Any]:
    validation = validar_serie_para_garch(portfolio_returns, min_obs=120, max_null_ratio=0.05)
    if not validation.get("ok", False):
        return {
            "comparison": pd.DataFrame(),
            "diagnostics": pd.DataFrame(),
            "summary_text": validation.get(
                "message",
                "No hay condiciones suficientes para estimar GARCH.",
            ),
            "persistencia": np.nan,
        }

    serie_garch = validation["serie_limpia"] * 100.0
    results = fit_garch_models(serie_garch)

    diagnostics = results.get("diagnostics", pd.DataFrame())
    persistencia = np.nan
    if not diagnostics.empty:
        mask = diagnostics["metrica"] == "persistencia_alpha_mas_beta"
        if mask.any():
            persistencia = pd.to_numeric(
                diagnostics.loc[mask, "valor"],
                errors="coerce",
            ).iloc[0]

    results["persistencia"] = persistencia
    return results


def _make_benchmark_adapter(rf_annual: float):
    def _adapter(portfolio_returns: pd.Series, benchmark_returns: Optional[pd.Series]) -> dict[str, Any]:
        if benchmark_returns is None or len(benchmark_returns) == 0:
            return {
                "benchmark_available": False,
                "tone": "neutral",
                "score": 50.0,
                "summary_text": "No hay benchmark disponible para comparación relativa.",
                "summary_df": pd.DataFrame(),
                "extras_df": pd.DataFrame(),
                "alpha_jensen": np.nan,
                "tracking_error": np.nan,
                "information_ratio": np.nan,
                "max_drawdown": np.nan,
            }

        try:
            summary_df, extras_df, _, _ = benchmark_summary(
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
                rf_annual=rf_annual,
            )
        except Exception as exc:
            return {
                "benchmark_available": False,
                "tone": "neutral",
                "score": 50.0,
                "summary_text": f"No fue posible construir el benchmark: {exc}",
                "summary_df": pd.DataFrame(),
                "extras_df": pd.DataFrame(),
                "alpha_jensen": np.nan,
                "tracking_error": np.nan,
                "information_ratio": np.nan,
                "max_drawdown": np.nan,
            }

        alpha_jensen = safe_metric(extras_df, "métrica", "Alpha de Jensen", "valor")
        tracking_error = safe_metric(extras_df, "métrica", "Tracking Error", "valor")
        information_ratio = safe_metric(extras_df, "métrica", "Information Ratio", "valor")
        max_drawdown = safe_metric(extras_df, "métrica", "Máximo drawdown", "valor")

        port_ret = safe_metric(summary_df, "serie", "Portafolio", "ret_acumulado")
        bench_ret = safe_metric(summary_df, "serie", "Benchmark", "ret_acumulado")

        if port_ret is not None and bench_ret is not None and port_ret > bench_ret and (alpha_jensen is None or alpha_jensen >= 0):
            tone = "positive"
            score = 78.0
            summary_text = "El portafolio muestra una lectura relativa favorable frente al benchmark."
        elif port_ret is not None and bench_ret is not None and port_ret < bench_ret and (alpha_jensen is None or alpha_jensen < 0):
            tone = "negative"
            score = 24.0
            summary_text = "El portafolio viene rezagado frente al benchmark en la ventana analizada."
        elif port_ret is not None and bench_ret is not None and port_ret >= bench_ret:
            tone = "slightly_positive"
            score = 62.0
            summary_text = "El portafolio mantiene una lectura ligeramente favorable frente al benchmark."
        else:
            tone = "neutral"
            score = 46.0
            summary_text = "La comparación relativa frente al benchmark es mixta o no concluyente."

        return {
            "benchmark_available": True,
            "tone": tone,
            "score": score,
            "summary_text": summary_text,
            "summary_df": summary_df,
            "extras_df": extras_df,
            "alpha_jensen": alpha_jensen,
            "tracking_error": tracking_error,
            "information_ratio": information_ratio,
            "max_drawdown": max_drawdown,
            "portfolio_total_return": port_ret,
            "benchmark_total_return": bench_ret,
            "excess_return": (port_ret - bench_ret) if port_ret is not None and bench_ret is not None else np.nan,
        }

    return _adapter


def _extract_persistencia(garch_results: dict[str, Any]) -> float:
    if not garch_results:
        return np.nan

    if "persistencia" in garch_results and garch_results["persistencia"] is not None:
        try:
            return float(garch_results["persistencia"])
        except Exception:
            pass

    diagnostics = garch_results.get("diagnostics", pd.DataFrame())
    if diagnostics is not None and not diagnostics.empty:
        mask = diagnostics["metrica"] == "persistencia_alpha_mas_beta"
        if mask.any():
            return pd.to_numeric(diagnostics.loc[mask, "valor"], errors="coerce").iloc[0]

    return np.nan


def _build_base100_series(
    portfolio_returns: pd.Series,
    benchmark_returns: Optional[pd.Series],
) -> tuple[Optional[pd.Series], Optional[pd.Series]]:
    if benchmark_returns is None or len(benchmark_returns) == 0:
        return None, None

    df = pd.concat([portfolio_returns, benchmark_returns], axis=1, join="inner").dropna()
    if df.empty:
        return None, None

    df.columns = ["portfolio", "benchmark"]
    cum_port = (1.0 + df["portfolio"]).cumprod() * 100.0
    cum_bench = (1.0 + df["benchmark"]).cumprod() * 100.0
    return cum_port, cum_bench


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

    .decision-pill-highlight {
        background: #FDF2F8;
        border: 1px solid rgba(157, 23, 77, 0.18);
        color: #831843 !important;
    }

    .decision-pill-highlight strong,
    .decision-pill-highlight span,
    .decision-pill-highlight div {
        color: #831843 !important;
    }
    </style>
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
    filtros_label="Parámetros Del Panel De Decisión",
    filtros_expanded=False,
)

# ==============================
# SIDEBAR
# ==============================
asset_name_by_ticker = {
    meta["ticker"]: asset_name
    for asset_name, meta in ASSETS.items()
}
all_tickers = list(asset_name_by_ticker.keys())

with filtros_sidebar:
    horizonte = st.selectbox(
        "Horizonte de análisis",
        [
            "1 mes",
            "Trimestre",
            "Semestre",
            "1 año",
            "3 años",
            "5 años",
            "Personalizado",
        ],
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
        "Activos del portafolio",
        options=all_tickers,
        default=all_tickers,
        format_func=lambda x: f"{x} · {asset_name_by_ticker.get(x, x)}",
        key="decision_tickers",
    )

    construction_choice = st.selectbox(
        "Objetivo de construcción del portafolio",
        [
            "Equiponderado",
            "Pesos manuales",
            "Mínima varianza",
            "Máxima utilidad",
        ],
        index=0,
        key="decision_construction_choice",
    )

    manual_weights_pct: dict[str, float] = {}
    manual_sum_pct = 0.0

    if construction_choice == "Pesos manuales" and selected_tickers:
        st.caption("Los pesos manuales deben sumar 100%.")

        n_assets = len(selected_tickers)
        default_equal = round(100.0 / n_assets, 2)

        for i, ticker in enumerate(selected_tickers):
            default_value = default_equal
            if i == n_assets - 1:
                default_value = max(0.0, round(100.0 - default_equal * (n_assets - 1), 2))

            manual_weights_pct[ticker] = st.number_input(
                f"Peso {ticker} (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(default_value),
                step=0.5,
                key=f"decision_manual_weight_{ticker}",
            )

        manual_sum_pct = float(sum(manual_weights_pct.values()))
        if np.isclose(manual_sum_pct, 100.0, atol=0.01):
            st.success(f"Suma actual: {manual_sum_pct:.2f}%")
        else:
            st.error(f"Suma actual: {manual_sum_pct:.2f}% · debe ser 100%.")

    utility_focus = 0.65
    if construction_choice == "Máxima utilidad":
        utility_focus = st.slider(
            "Énfasis retorno-utilidad",
            min_value=0.50,
            max_value=0.95,
            value=0.65,
            step=0.05,
            key="decision_utility_focus",
            help="Valores más altos dan más peso al retorno esperado frente a la componente defensiva.",
        )

    benchmark_option = st.selectbox(
        "Benchmark",
        [GLOBAL_BENCHMARK, "Sin benchmark"],
        index=0,
        key="decision_benchmark",
    )

    mostrar_tablas = st.checkbox("Mostrar tablas completas", value=False, key="decision_show_tables")

    with st.expander("Filtros secundarios", expanded=False):
        confidence_level = st.select_slider(
            "Nivel de confianza VaR / CVaR",
            options=[0.95, 0.96, 0.97, 0.98, 0.99],
            value=0.95,
            format_func=lambda x: f"{x:.0%}",
            key="decision_conf",
        )
        n_sim = st.slider(
            "Simulaciones Monte Carlo",
            min_value=5000,
            max_value=50000,
            value=10000,
            step=5000,
            key="decision_nsim",
        )
        if modo == "Estadístico":
            mostrar_diagnostico = st.checkbox(
                "Mostrar diagnóstico técnico",
                value=True,
                key="decision_show_diag",
            )
        else:
            mostrar_diagnostico = st.checkbox(
                "Mostrar diagnóstico técnico",
                value=False,
                key="decision_show_diag_gen",
            )

# ==============================
# VALIDACIONES
# ==============================
if not selected_tickers:
    st.error("Debes seleccionar al menos un activo para construir el portafolio.")
    st.stop()

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

if construction_choice == "Pesos manuales" and not np.isclose(manual_sum_pct, 100.0, atol=0.01):
    st.error("Con pesos manuales, la suma debe ser exactamente 100%.")
    st.stop()

# ==============================
# DATOS
# ==============================
bundle = load_market_bundle(
    tickers=selected_tickers,
    start=str(start_date),
    end=str(end_date),
)

returns = bundle["returns"].replace([np.inf, -np.inf], np.nan).dropna(how="any")
prices_df = _extract_prices_from_bundle(bundle, selected_tickers)

if returns.empty or len(returns) < 30:
    st.error("No hay suficientes datos para construir el panel de decisión.")
    st.stop()

if prices_df.empty:
    prices_df = pd.DataFrame(index=returns.index, columns=selected_tickers, data=np.nan)

macro = _get_macro()
rf_annual = _get_rf_annual(macro)

rf_pct = macro.get("risk_free_rate_pct", np.nan)
rf_pct = float(rf_pct) if pd.notna(rf_pct) else None

inflation_yoy = macro.get("inflation_yoy", np.nan)
inflation_yoy = float(inflation_yoy) if pd.notna(inflation_yoy) else None

usdcop_market = macro.get("usdcop_market", np.nan)
usdcop_market = float(usdcop_market) if pd.notna(usdcop_market) else None

cop_per_usd = macro.get("cop_per_usd", np.nan)
cop_per_usd = float(cop_per_usd) if pd.notna(cop_per_usd) else None

benchmark_returns = None
if benchmark_option != "Sin benchmark":
    benchmark_returns = _download_benchmark_returns(benchmark_option, start_date, end_date)

weighting_mode, manual_weights, markowitz_weights, portfolio_weights_preview = _resolve_portfolio_construction(
    selected_tickers=selected_tickers,
    returns_df=returns,
    construction_choice=construction_choice,
    manual_weights_pct=manual_weights_pct,
    rf_annual=rf_annual,
    utility_focus=utility_focus,
)

investor_profile = "balanceado"
custom_profile = None

signal_adapter = _make_signal_adapter(start_date, end_date)
var_cvar_adapter = _make_var_cvar_adapter(returns, portfolio_weights_preview, n_sim)
benchmark_adapter = _make_benchmark_adapter(rf_annual)

engine_inputs = DecisionEngineInputs(
    tickers=selected_tickers,
    prices_df=prices_df,
    returns_df=returns,
    weighting_mode=weighting_mode,
    manual_weights=manual_weights,
    markowitz_weights=markowitz_weights,
    investor_profile=investor_profile,
    custom_profile=custom_profile,
    confidence_level=confidence_level,
    benchmark_returns=benchmark_returns,
)

engine_deps = EngineDependencies(
    var_cvar_func=var_cvar_adapter,
    garch_func=_garch_adapter,
    benchmark_func=benchmark_adapter,
    signals_func=signal_adapter,
)

try:
    engine_result = run_decision_engine(engine_inputs, engine_deps)
except Exception as exc:
    st.error(f"No fue posible construir el panel de decisión: {exc}")
    st.stop()

# ==============================
# RESULTADOS
# ==============================
final_decision = engine_result.final_decision
objective_risk = engine_result.objective_risk
signal_summary = engine_result.signal_summary
benchmark_summary_dict = engine_result.benchmark_summary
garch_results = engine_result.garch_results

weights_df = engine_result.weights_df.copy()
metrics_df = engine_result.metrics_df.copy()
scorecard_df = engine_result.scorecard_df.copy()
selective_buys_df = engine_result.selective_buys_df.copy()

metrics_map = dict(zip(metrics_df["Metrica"], metrics_df["Valor"]))
garch_persistencia = _extract_persistencia(garch_results)

benchmark_detail_df = benchmark_summary_dict.get("summary_df", pd.DataFrame())
benchmark_extras_df = benchmark_summary_dict.get("extras_df", pd.DataFrame())
signal_table = signal_summary.get("signal_table", pd.DataFrame())

alpha_jensen = benchmark_summary_dict.get("alpha_jensen", np.nan)
tracking_error = benchmark_summary_dict.get("tracking_error", np.nan)
information_ratio = benchmark_summary_dict.get("information_ratio", np.nan)
max_drawdown = benchmark_summary_dict.get("max_drawdown", np.nan)
ret_port = benchmark_summary_dict.get("portfolio_total_return", np.nan)
ret_bench = benchmark_summary_dict.get("benchmark_total_return", np.nan)

favorable_ratio = signal_summary.get("favorable_ratio", np.nan)
balance_signals = len(signal_summary.get("favorables_en_portafolio", [])) - len(signal_summary.get("desfavorables_en_portafolio", []))

cum_port, cum_bench = _build_base100_series(
    engine_result.portfolio_returns,
    benchmark_returns,
)

construction_mode_label = {
    "equal": "Equiponderado",
    "manual": "Pesos manuales",
    "markowitz": "Optimizado",
}.get(weighting_mode, "N/D")

construction_objective_label = {
    "Equiponderado": "Equiponderado",
    "Pesos manuales": "Pesos manuales",
    "Mínima varianza": "Mínima varianza",
    "Máxima utilidad": "Máxima utilidad",
}.get(construction_choice, construction_choice)

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 9 - Panel de decisión",
    "Integra riesgo, VaR, CVaR, GARCH, benchmark y señales para producir una postura final coherente con una regla base estable y con un objetivo de construcción separado",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo separa dos capas: el objetivo de construcción define los pesos del portafolio, mientras la regla del motor traduce ese diagnóstico en una postura final estable."
    )
else:
    nota(
        "En modo estadístico, el panel separa construcción y decisión. El riesgo objetivo del portafolio surge de la construcción elegida; la postura final se obtiene aplicando una regla base estable del motor."
    )

if macro.get("source"):
    st.caption(f"Fuente macro: {macro['source']}")
if macro.get("last_updated"):
    st.caption(f"Última actualización macro: {macro['last_updated']}")

# ==============================
# RESUMEN
# ==============================
seccion("Resumen Del Módulo")

if modo == "General":
    nota(
        "La decisión final se construye con tres pilares: riesgo objetivo del portafolio, lectura técnica agregada y comparación frente al benchmark. Los pesos dependen de la construcción elegida y no de un filtro de perfil."
    )
else:
    nota(
        "Metodológicamente, el panel corrige el problema conceptual original: la decisión ya no depende de un filtro subjetivo visible, sino de una regla estable aplicada sobre un portafolio construido con un objetivo explícito."
    )

st.markdown(
    f"""
    <div class="decision-meta-row">
        <div class="decision-mini-meta"><strong>Horizonte:</strong>&nbsp;{horizonte}</div>
        <div class="decision-mini-meta"><strong>Inicio:</strong>&nbsp;{start_date}</div>
        <div class="decision-mini-meta"><strong>Fin:</strong>&nbsp;{end_date}</div>
        <div class="decision-mini-meta decision-pill-highlight"><strong>Construcción:</strong>&nbsp;{construction_objective_label}</div>
        <div class="decision-mini-meta"><strong>Modo pesos:</strong>&nbsp;{construction_mode_label}</div>
        <div class="decision-mini-meta"><strong>Benchmark:</strong>&nbsp;{benchmark_option}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================
# TABS
# ==============================
tab1, tab2, tab3 = st.tabs([
    "Decisión integrada",
    "Métricas de soporte",
    "Tablas e interpretación",
])

# ==============================
# TAB 1
# ==============================
with tab1:
    seccion("Postura Final Del Motor")

    if modo == "General":
        nota(
            "La salida del panel es una postura operativa clara. La construcción elegida define los pesos; la regla base del motor define cómo actuar frente al riesgo que esos pesos generan."
        )
    else:
        nota(
            "La postura final surge de un score objetivo del portafolio y de una regla base de decisión. Los pesos pertenecen a la capa de construcción; la acción pertenece a la capa de decisión."
        )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta_kpi(
            "Postura final",
            final_decision["stance"],
            final_decision["action"],
            help_text="Conclusión operativa del motor de decisión.",
            subtexto="Es la recomendación final bajo una regla base estable.",
        )

    with c2:
        tarjeta_kpi(
            "Riesgo objetivo",
            objective_risk["risk_label"],
            f"Score {objective_risk['risk_score']}",
            help_text="Clasificación objetiva del riesgo del portafolio.",
            subtexto="Cambia con la construcción, no por un filtro de perfil.",
        )

    with c3:
        tarjeta_kpi(
            "Construcción",
            construction_objective_label,
            help_text="Criterio que define los pesos del portafolio.",
            subtexto="Separado de la postura final del motor.",
        )

    with c4:
        tarjeta_kpi(
            "Compras selectivas",
            str(len(selective_buys_df)),
            "Tickers sugeridos" if not selective_buys_df.empty else "Sin candidatos",
            help_text="Número de activos con señal favorable y consistencia con el portafolio.",
            subtexto="Se listan activos concretos y no texto genérico.",
        )

    plot_card_footer(final_decision["explanation"])

    seccion("Regla De Decisión Del Motor")
    nota(
        "En esta versión, el panel no expone un filtro de perfil del inversor. La decisión final se construye con una regla base estable y coherente, separada de la construcción de pesos del portafolio."
    )

    seccion("Señales Y Compras Selectivas")

    s1, s2, s3 = st.columns(3)

    with s1:
        tarjeta_kpi(
            "Lectura técnica",
            signal_label(signal_summary.get("tone", "neutral")),
            delta_label(
                balance_signals,
                "Sesgo comprador",
                "Sesgo vendedor",
                "Balance neutro",
            ),
            help_text="Resumen agregado de señales del portafolio.",
            subtexto="Se construye a partir de señales favorables, neutrales y desfavorables.",
        )

    with s2:
        tarjeta_kpi(
            "Proporción favorable",
            f"{favorable_ratio:.2%}" if pd.notna(favorable_ratio) else "N/D",
            help_text="Porcentaje de activos del portafolio con señal favorable.",
            subtexto="Se utiliza dentro de la regla final de decisión.",
        )

    with s3:
        tarjeta_kpi(
            "Benchmark relativo",
            benchmark_label(benchmark_summary_dict.get("tone", "neutral")),
            help_text="Lectura comparativa del portafolio frente al benchmark.",
            subtexto=benchmark_summary_dict.get("summary_text", "Sin comparación disponible."),
        )

    if not selective_buys_df.empty:
        st.markdown("#### Tickers sugeridos para compra selectiva")
        st.dataframe(selective_buys_df, use_container_width=True, hide_index=True)
    else:
        nota(
            "No se identificaron compras selectivas consistentes con las señales y con la composición actual del portafolio."
        )

# ==============================
# TAB 2
# ==============================
with tab2:
    seccion("KPIs De Soporte Cuantitativo")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        tarjeta_kpi(
            "VaR",
            f"{metrics_map.get(f'VaR ({confidence_level:.0%})', np.nan):.2%}" if pd.notna(metrics_map.get(f"VaR ({confidence_level:.0%})", np.nan)) else "N/D",
            help_text="Pérdida umbral estimada del portafolio.",
            subtexto="Se incorpora en la clasificación objetiva del riesgo.",
        )

    with k2:
        tarjeta_kpi(
            "CVaR",
            f"{metrics_map.get(f'CVaR ({confidence_level:.0%})', np.nan):.2%}" if pd.notna(metrics_map.get(f"CVaR ({confidence_level:.0%})", np.nan)) else "N/D",
            help_text="Pérdida esperada condicional en cola.",
            subtexto="Captura severidad promedio en escenarios extremos.",
        )

    with k3:
        tarjeta_kpi(
            "Volatilidad anualizada",
            f"{metrics_map.get('Volatilidad anualizada', np.nan):.2%}" if pd.notna(metrics_map.get("Volatilidad anualizada", np.nan)) else "N/D",
            help_text="Volatilidad anual del portafolio.",
            subtexto="También participa en la clasificación objetiva del riesgo.",
        )

    with k4:
        tarjeta_kpi(
            "Persistencia GARCH",
            f"{garch_persistencia:.3f}" if pd.notna(garch_persistencia) else "N/D",
            delta_label(
                (0.90 - garch_persistencia) if pd.notna(garch_persistencia) else None,
                "Persistencia moderada",
                "Persistencia alta",
                "Persistencia límite",
            ),
            help_text="Memoria de la volatilidad condicional del portafolio.",
            subtexto="Apoya la lectura dinámica del riesgo.",
        )

    plot_card_footer(objective_risk["rationale"])

    seccion("Benchmark Y Contexto Macro")

    b1, b2, b3, b4 = st.columns(4)

    with b1:
        tarjeta_kpi(
            "Retorno portafolio",
            f"{ret_port:.2%}" if pd.notna(ret_port) else "N/D",
            help_text="Retorno acumulado del portafolio frente al benchmark.",
            subtexto="Permite evaluar generación de valor relativa.",
        )

    with b2:
        tarjeta_kpi(
            "Alpha de Jensen",
            f"{alpha_jensen:.4f}" if pd.notna(alpha_jensen) else "N/D",
            delta_label(alpha_jensen, "Alpha positivo", "Alpha negativo", "Alpha neutro"),
            help_text="Exceso de desempeño ajustado por riesgo sistemático.",
            subtexto="Resume si el portafolio agregó valor frente a lo esperado por CAPM.",
        )

    with b3:
        tarjeta_kpi(
            "Tracking Error",
            f"{tracking_error:.4f}" if pd.notna(tracking_error) else "N/D",
            help_text="Desviación del portafolio frente al benchmark.",
            subtexto="Cuantifica riesgo activo relativo.",
        )

    with b4:
        tarjeta_kpi(
            "Information Ratio",
            f"{information_ratio:.4f}" if pd.notna(information_ratio) else "N/D",
            delta_label(
                information_ratio,
                "Retorno activo eficiente",
                "Retorno activo débil",
                "Lectura neutral",
            ),
            help_text="Retorno activo por unidad de tracking error.",
            subtexto="Mide eficiencia del desempeño relativo.",
        )

    plot_card_footer(
        interpret_relative_performance(ret_port, ret_bench, alpha_jensen, tracking_error)
    )

    seccion("Comparación Visual")

    if cum_port is not None and cum_bench is not None:
        plot_card_header(
            "Portafolio vs benchmark",
            "El gráfico base 100 permite comparar el desempeño acumulado del portafolio frente al benchmark dentro del mismo horizonte del motor.",
            modo=modo,
            caption="Sirve para validar si la postura final también es consistente con la lectura relativa de desempeño.",
        )

        toolbar_label("Opciones de visualización")
        g1, g2 = st.columns(2)
        with g1:
            clean_chart = st.checkbox("Vista limpia", value=False, key="decision_clean_chart")
        with g2:
            show_interpretation_box = st.checkbox("Mostrar guía de lectura", value=True, key="decision_show_chart_guide")

        fig_benchmark = plot_benchmark_base100(cum_port, cum_bench)
        fig_benchmark = style_plot(fig_benchmark, modo)
        fig_benchmark.update_layout(
            title=dict(
                text="Portafolio Vs Benchmark (Base 100)",
                x=0.03,
                xanchor="left",
                y=0.97,
                yanchor="top",
                font=dict(size=16, color="#0F172A"),
            ),
            margin=dict(l=20, r=20, t=70, b=20),
        )

        if clean_chart:
            try:
                fig_benchmark.update_layout(showlegend=False)
            except Exception:
                pass

        st.plotly_chart(fig_benchmark, use_container_width=True)

        if show_interpretation_box:
            if modo == "General":
                plot_card_footer(
                    "Si la línea del portafolio termina por encima del benchmark, hubo mejor desempeño acumulado. Si ambas series se mueven de forma muy parecida, la cartera siguió de cerca al índice. Caídas profundas reflejan episodios de mayor presión de riesgo."
                )
            else:
                plot_card_footer(
                    "La separación entre curvas refleja desempeño relativo acumulado. La amplitud de las caídas ayuda a identificar drawdowns y sensibilidad del portafolio frente a choques de mercado."
                )
    else:
        nota("No fue posible construir una comparación visual robusta frente al benchmark para este periodo.")

    seccion("Lectura Macro Complementaria")
    plot_card_footer(interpret_macro_context(rf_pct, inflation_yoy, usdcop_market, cop_per_usd))

# ==============================
# TAB 3
# ==============================
with tab3:
    seccion("Tablas Del Motor")

    if mostrar_tablas:
        st.markdown("#### Pesos del portafolio")
        st.dataframe(weights_df, use_container_width=True, hide_index=True)

        st.markdown("#### Scorecard del motor")
        st.dataframe(scorecard_df, use_container_width=True, hide_index=True)

        st.markdown("#### Métricas del portafolio")
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    else:
        with st.expander("Ver tablas principales del motor"):
            st.markdown("#### Pesos del portafolio")
            st.dataframe(weights_df, use_container_width=True, hide_index=True)

            st.markdown("#### Scorecard del motor")
            st.dataframe(scorecard_df, use_container_width=True, hide_index=True)

            st.markdown("#### Métricas del portafolio")
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    seccion("Interpretación Final")

    if modo == "General":
        nota(
            f"La postura final del panel es **{final_decision['stance']}**. El riesgo objetivo del portafolio se clasifica como **{objective_risk['risk_label']}**, y esa medición depende de la construcción seleccionada, no de un filtro de perfil."
        )
        nota(
            f"La construcción seleccionada fue **{construction_objective_label}**. El motor concluye: {final_decision['explanation']}"
        )
    else:
        nota(
            "Desde el punto de vista metodológico, el módulo 09 ya no mezcla preferencia del usuario con construcción de pesos. El portafolio se construye primero y luego el motor aplica una regla base estable de decisión."
        )
        nota(
            f"En esta corrida, la construcción elegida fue **{construction_objective_label}**, el riesgo objetivo resultante fue **{objective_risk['risk_label']}** y el puntaje base fue **{final_decision['base_score']:.1f}**, produciendo la postura final **{final_decision['stance']}**."
        )

    if mostrar_diagnostico:
        seccion("Diagnóstico Técnico Adicional")

        with st.expander("Ver señales por ticker", expanded=False):
            if isinstance(signal_table, pd.DataFrame) and not signal_table.empty:
                st.dataframe(signal_table, use_container_width=True, hide_index=True)
            else:
                st.info("No hay tabla detallada de señales disponible.")

        with st.expander("Ver benchmark detallado", expanded=False):
            if isinstance(benchmark_detail_df, pd.DataFrame) and not benchmark_detail_df.empty:
                st.dataframe(benchmark_detail_df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay tabla principal de benchmark disponible.")

            if isinstance(benchmark_extras_df, pd.DataFrame) and not benchmark_extras_df.empty:
                st.dataframe(benchmark_extras_df, use_container_width=True, hide_index=True)

        with st.expander("Ver diagnósticos GARCH", expanded=False):
            diagnostics_df = garch_results.get("diagnostics", pd.DataFrame())
            comparison_df = garch_results.get("comparison", pd.DataFrame())
            summary_text = garch_results.get("summary_text", "")

            if isinstance(diagnostics_df, pd.DataFrame) and not diagnostics_df.empty:
                st.dataframe(diagnostics_df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay diagnósticos GARCH disponibles para la serie analizada.")

            if isinstance(comparison_df, pd.DataFrame) and not comparison_df.empty:
                st.dataframe(comparison_df, use_container_width=True, hide_index=True)

            if summary_text:
                st.caption(summary_text)

    if engine_result.warnings:
        with st.expander("Ver advertencias del motor", expanded=False):
            for warning in engine_result.warnings:
                st.warning(warning)