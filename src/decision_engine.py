from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd


# ============================================================
#  CONFIGURACIÓN DE PERFILES
#  El perfil NO cambia la medición objetiva del riesgo.
#  Solo modifica la regla de decisión final.
# ============================================================

PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "conservador": {
        "nombre": "Conservador",
        "descripcion": (
            "Prioriza preservación de capital y estabilidad. "
            "Tolera poco deterioro del portafolio."
        ),
        "que_modifica": (
            "Endurece la regla final de compra: exige menor riesgo objetivo, "
            "mejor consistencia de señales y mejor comportamiento frente al benchmark."
        ),
        "por_que_se_llama_asi": (
            "Se llama conservador porque la postura final evita ampliar exposición "
            "cuando el portafolio presenta riesgo elevado o señales mixtas."
        ),
        "max_risk_for_buy": 2,              # 1=Bajo, 2=Moderado, 3=Alto, 4=Muy alto
        "buy_threshold": 72.0,
        "hold_threshold": 55.0,
        "min_favorable_ratio": 0.50,
        "require_non_negative_benchmark": True,
        "allow_tactical_buy_on_high_risk": False,
    },
    "balanceado": {
        "nombre": "Balanceado",
        "descripcion": (
            "Busca equilibrio entre crecimiento y control del riesgo."
        ),
        "que_modifica": (
            "Usa una regla intermedia: puede aceptar riesgo moderado y señales mixtas "
            "si el puntaje agregado del portafolio es razonable."
        ),
        "por_que_se_llama_asi": (
            "Se llama balanceado porque no maximiza ni la prudencia extrema "
            "ni la agresividad táctica."
        ),
        "max_risk_for_buy": 2,
        "buy_threshold": 64.0,
        "hold_threshold": 48.0,
        "min_favorable_ratio": 0.40,
        "require_non_negative_benchmark": False,
        "allow_tactical_buy_on_high_risk": False,
    },
    "agresivo": {
        "nombre": "Agresivo",
        "descripcion": (
            "Acepta más volatilidad y drawdown potencial si la lectura táctica "
            "y la oportunidad relativa lo justifican."
        ),
        "que_modifica": (
            "Relaja la regla final de compra: admite riesgo alto siempre que "
            "las señales y el puntaje base del portafolio sean suficientemente fuertes."
        ),
        "por_que_se_llama_asi": (
            "Se llama agresivo porque la postura final permite actuar incluso "
            "con mayor incertidumbre, pero sin alterar la medición objetiva del riesgo."
        ),
        "max_risk_for_buy": 3,
        "buy_threshold": 56.0,
        "hold_threshold": 40.0,
        "min_favorable_ratio": 0.34,
        "require_non_negative_benchmark": False,
        "allow_tactical_buy_on_high_risk": True,
    },
}

DEFAULT_CUSTOM_PROFILE = {
    "nombre": "Personalizado",
    "descripcion": (
        "Perfil definido por parámetros de tolerancia elegidos por el usuario."
    ),
    "que_modifica": (
        "Modifica la regla final de decisión según umbrales configurados "
        "por el usuario, sin alterar la medición objetiva del riesgo."
    ),
    "por_que_se_llama_asi": (
        "Se llama personalizado porque la política final no sigue un perfil fijo."
    ),
    "max_risk_for_buy": 2,
    "buy_threshold": 62.0,
    "hold_threshold": 46.0,
    "min_favorable_ratio": 0.40,
    "require_non_negative_benchmark": False,
    "allow_tactical_buy_on_high_risk": False,
}


# ============================================================
#  DATACLASSES DE ENTRADA / SALIDA
# ============================================================

@dataclass
class EngineDependencies:
    """
    Hooks opcionales para reutilizar módulos existentes del proyecto.
    Así evitas duplicar cálculos que ya tienes en otros archivos.
    """
    var_cvar_func: Optional[Callable[[pd.Series, float], dict[str, Any]]] = None
    garch_func: Optional[Callable[[pd.Series], dict[str, Any]]] = None
    benchmark_func: Optional[Callable[[pd.Series, Optional[pd.Series]], dict[str, Any]]] = None
    signals_func: Optional[Callable[[pd.DataFrame, list[str]], dict[str, Any]]] = None
    markowitz_func: Optional[Callable[..., dict[str, float]]] = None


@dataclass
class DecisionEngineInputs:
    tickers: list[str]
    prices_df: Optional[pd.DataFrame] = None
    returns_df: Optional[pd.DataFrame] = None

    weighting_mode: str = "equal"          # equal | manual | markowitz
    manual_weights: Optional[dict[str, float]] = None
    markowitz_weights: Optional[dict[str, float]] = None

    investor_profile: str = "balanceado"   # conservador | balanceado | agresivo | personalizado
    custom_profile: Optional[dict[str, Any]] = None

    confidence_level: float = 0.95
    benchmark_returns: Optional[pd.Series] = None

    # Si ya vienes con resultados previos desde otros módulos, los pasas acá
    var_cvar_results: Optional[dict[str, Any]] = None
    garch_results: Optional[dict[str, Any]] = None
    benchmark_summary: Optional[dict[str, Any]] = None
    signal_summary: Optional[dict[str, Any]] = None


@dataclass
class DecisionEngineResult:
    weights: pd.Series
    portfolio_returns: pd.Series
    weights_df: pd.DataFrame
    metrics_df: pd.DataFrame
    scorecard_df: pd.DataFrame
    selective_buys_df: pd.DataFrame

    objective_risk: dict[str, Any]
    profile_info: dict[str, Any]
    signal_summary: dict[str, Any]
    benchmark_summary: dict[str, Any]
    garch_results: dict[str, Any]
    final_decision: dict[str, Any]

    warnings: list[str] = field(default_factory=list)


# ============================================================
#  HELPERS GENERALES
# ============================================================

RISK_LABELS = {
    1: "Bajo",
    2: "Moderado",
    3: "Alto",
    4: "Muy alto",
}

RISK_SCORE_TO_POINTS = {
    1: 90.0,
    2: 70.0,
    3: 40.0,
    4: 15.0,
}


def _clean_tickers(tickers: list[str]) -> list[str]:
    clean = [str(t).strip().upper() for t in tickers if str(t).strip()]
    seen: set[str] = set()
    out: list[str] = []
    for t in clean:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


def _to_series(values: Any, name: str = "x") -> pd.Series:
    if isinstance(values, pd.Series):
        s = values.copy()
    elif isinstance(values, (list, tuple, np.ndarray)):
        s = pd.Series(values, name=name)
    else:
        raise ValueError(f"No se pudo convertir {name} a Series.")
    s = pd.to_numeric(s, errors="coerce").dropna()
    return s


def _first_existing(d: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    for key in keys:
        if key in d and d[key] is not None:
            return d[key]
    return default


def _first_numeric(d: dict[str, Any], keys: list[str], default: Optional[float] = None) -> Optional[float]:
    for key in keys:
        if key in d and d[key] is not None:
            try:
                return float(d[key])
            except Exception:
                pass

    # búsqueda recursiva simple en subdicts
    for value in d.values():
        if isinstance(value, dict):
            val = _first_numeric(value, keys, default=None)
            if val is not None:
                return val

    return default


def _coerce_price_or_return_frame(
    tickers: list[str],
    prices_df: Optional[pd.DataFrame],
    returns_df: Optional[pd.DataFrame],
) -> tuple[Optional[pd.DataFrame], pd.DataFrame]:
    """
    Devuelve:
    - price_frame_filtrado (si existe)
    - returns_frame_filtrado
    """
    clean_tickers = _clean_tickers(tickers)

    if returns_df is not None and not returns_df.empty:
        rf = returns_df.copy()
        available = [t for t in clean_tickers if t in rf.columns]
        if not available:
            raise ValueError("No hay columnas de retornos compatibles con los tickers seleccionados.")
        rf = rf[available].apply(pd.to_numeric, errors="coerce").dropna(how="all")
        return None, rf

    if prices_df is None or prices_df.empty:
        raise ValueError("Debes proporcionar prices_df o returns_df para construir el portafolio.")

    pf = prices_df.copy()
    available = [t for t in clean_tickers if t in pf.columns]
    if not available:
        raise ValueError("No hay columnas de precios compatibles con los tickers seleccionados.")

    pf = pf[available].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    rf = pf.pct_change().dropna(how="all")
    return pf, rf


# ============================================================
#  CONSTRUCCIÓN DE PESOS
# ============================================================

def normalize_weights(weights: pd.Series) -> pd.Series:
    w = pd.to_numeric(weights, errors="coerce").fillna(0.0).astype(float)
    if (w < 0).any():
        raise ValueError("No se permiten pesos negativos.")
    total = float(w.sum())
    if total <= 0:
        raise ValueError("La suma de pesos debe ser positiva.")

    # Acepta pesos que sumen 1 o 100
    if np.isclose(total, 100.0, atol=1e-8):
        w = w / 100.0
    elif not np.isclose(total, 1.0, atol=1e-8):
        raise ValueError("Los pesos manuales deben sumar 1.0 o 100.0.")

    return w / w.sum()


def build_portfolio_weights(
    tickers: list[str],
    mode: str = "equal",
    manual_weights: Optional[dict[str, float]] = None,
    markowitz_weights: Optional[dict[str, float]] = None,
) -> pd.Series:
    clean_tickers = _clean_tickers(tickers)
    if not clean_tickers:
        raise ValueError("Debes seleccionar al menos un ticker.")

    mode = str(mode).strip().lower()

    if mode == "equal":
        weights = pd.Series(1.0 / len(clean_tickers), index=clean_tickers, name="weight")
        return weights

    if mode == "manual":
        if not manual_weights:
            raise ValueError("Seleccionaste pesos manuales, pero no enviaste manual_weights.")
        raw = pd.Series(manual_weights, dtype=float)
        raw.index = [str(i).strip().upper() for i in raw.index]
        raw = raw.reindex(clean_tickers).fillna(0.0)
        weights = normalize_weights(raw)
        weights.name = "weight"
        return weights

    if mode == "markowitz":
        if not markowitz_weights:
            raise ValueError(
                "Seleccionaste modo Markowitz, pero no enviaste markowitz_weights. "
                "Deja preparada la conexión o usa equal/manual."
            )
        raw = pd.Series(markowitz_weights, dtype=float)
        raw.index = [str(i).strip().upper() for i in raw.index]
        raw = raw.reindex(clean_tickers).fillna(0.0)
        weights = normalize_weights(raw)
        weights.name = "weight"
        return weights

    raise ValueError(f"Modo de pesos no soportado: {mode}")


def compute_portfolio_returns(
    returns_df: pd.DataFrame,
    weights: pd.Series,
) -> pd.Series:
    common = [c for c in weights.index if c in returns_df.columns]
    if not common:
        raise ValueError("No hay columnas comunes entre retornos y pesos del portafolio.")

    aligned_returns = returns_df[common].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    aligned_weights = weights[common].astype(float)

    portfolio_returns = aligned_returns.mul(aligned_weights, axis=1).sum(axis=1)
    portfolio_returns.name = "portfolio_return"
    return portfolio_returns.dropna()


# ============================================================
#  MÉTRICAS BASE DEL PORTAFOLIO
# ============================================================

def historical_var_cvar(returns: pd.Series, confidence_level: float = 0.95) -> dict[str, Any]:
    s = _to_series(returns, "portfolio_returns")
    if s.empty:
        return {"var": np.nan, "cvar": np.nan, "method": "historical"}

    alpha = 1.0 - confidence_level
    var_cut = float(s.quantile(alpha))
    tail = s[s <= var_cut]

    return {
        "var": abs(var_cut),
        "cvar": abs(float(tail.mean())) if not tail.empty else abs(var_cut),
        "confidence_level": confidence_level,
        "method": "historical",
    }


def default_benchmark_summary(
    portfolio_returns: pd.Series,
    benchmark_returns: Optional[pd.Series],
) -> dict[str, Any]:
    if benchmark_returns is None or len(benchmark_returns) == 0:
        return {
            "benchmark_available": False,
            "portfolio_total_return": float((1.0 + portfolio_returns).prod() - 1.0),
            "benchmark_total_return": np.nan,
            "excess_return": np.nan,
            "tracking_error_ann": np.nan,
            "information_ratio": np.nan,
            "tone": "neutral",
            "score": 50.0,
            "summary_text": "No hay benchmark disponible para comparación relativa.",
        }

    p = _to_series(portfolio_returns, "portfolio_returns")
    b = _to_series(benchmark_returns, "benchmark_returns")
    df = pd.concat([p, b], axis=1, join="inner").dropna()
    df.columns = ["portfolio", "benchmark"]

    if df.empty:
        return {
            "benchmark_available": False,
            "portfolio_total_return": float((1.0 + p).prod() - 1.0) if not p.empty else np.nan,
            "benchmark_total_return": np.nan,
            "excess_return": np.nan,
            "tracking_error_ann": np.nan,
            "information_ratio": np.nan,
            "tone": "neutral",
            "score": 50.0,
            "summary_text": "No hubo solapamiento suficiente entre portafolio y benchmark.",
        }

    active = df["portfolio"] - df["benchmark"]
    total_p = float((1.0 + df["portfolio"]).prod() - 1.0)
    total_b = float((1.0 + df["benchmark"]).prod() - 1.0)
    excess = total_p - total_b

    tracking_error_ann = float(active.std(ddof=1) * np.sqrt(252)) if len(active) > 1 else np.nan
    ir = float((active.mean() * 252) / tracking_error_ann) if tracking_error_ann and tracking_error_ann > 0 else np.nan

    if excess > 0.03:
        tone, score = "positive", 78.0
    elif excess >= 0.0:
        tone, score = "slightly_positive", 62.0
    elif excess > -0.03:
        tone, score = "neutral", 46.0
    else:
        tone, score = "negative", 24.0

    return {
        "benchmark_available": True,
        "portfolio_total_return": total_p,
        "benchmark_total_return": total_b,
        "excess_return": excess,
        "tracking_error_ann": tracking_error_ann,
        "information_ratio": ir,
        "tone": tone,
        "score": score,
        "summary_text": (
            f"El portafolio {'supera' if excess >= 0 else 'queda por debajo de'} "
            f"su benchmark en {excess:.2%}."
        ),
    }


def summarize_signals(
    signal_summary: Optional[dict[str, Any]],
    tickers: list[str],
    weights: pd.Series,
) -> dict[str, Any]:
    tickers = _clean_tickers(tickers)
    signal_summary = signal_summary or {}

    favorable = _first_existing(
        signal_summary,
        ["favorables_tickers", "favorable_tickers", "buy_tickers", "bullish_tickers"],
        default=[],
    )
    unfavorable = _first_existing(
        signal_summary,
        ["desfavorables_tickers", "unfavorable_tickers", "sell_tickers", "bearish_tickers"],
        default=[],
    )
    neutral = _first_existing(
        signal_summary,
        ["neutrales_tickers", "neutral_tickers", "hold_tickers"],
        default=[],
    )

    favorable = _clean_tickers(list(favorable))
    unfavorable = _clean_tickers(list(unfavorable))
    neutral = _clean_tickers(list(neutral))

    in_portfolio_favorable = [t for t in favorable if t in tickers]
    in_portfolio_unfavorable = [t for t in unfavorable if t in tickers]
    in_portfolio_neutral = [t for t in neutral if t in tickers]

    n = max(len(tickers), 1)
    favorable_ratio = len(in_portfolio_favorable) / n
    unfavorable_ratio = len(in_portfolio_unfavorable) / n

    net_signal = len(in_portfolio_favorable) - len(in_portfolio_unfavorable)
    raw_score = 50.0 + 35.0 * favorable_ratio - 25.0 * unfavorable_ratio + 5.0 * np.sign(net_signal)
    score = float(np.clip(raw_score, 0.0, 100.0))

    if score >= 70:
        tone = "strong_positive"
    elif score >= 55:
        tone = "positive"
    elif score >= 45:
        tone = "neutral"
    elif score >= 30:
        tone = "negative"
    else:
        tone = "strong_negative"

    return {
        **signal_summary,
        "favorables_tickers": favorable,
        "desfavorables_tickers": unfavorable,
        "neutrales_tickers": neutral,
        "favorables_en_portafolio": in_portfolio_favorable,
        "desfavorables_en_portafolio": in_portfolio_unfavorable,
        "neutrales_en_portafolio": in_portfolio_neutral,
        "favorable_ratio": favorable_ratio,
        "unfavorable_ratio": unfavorable_ratio,
        "score": score,
        "tone": tone,
        "summary_text": (
            f"Se detectan {len(in_portfolio_favorable)} activos favorables, "
            f"{len(in_portfolio_unfavorable)} desfavorables y "
            f"{len(in_portfolio_neutral)} neutrales dentro del portafolio."
        ),
    }


def build_selective_buys(
    signal_summary: dict[str, Any],
    weights: pd.Series,
) -> pd.DataFrame:
    favorable = signal_summary.get("favorables_en_portafolio", []) or []
    unfavorable = set(signal_summary.get("desfavorables_en_portafolio", []) or [])

    rows: list[dict[str, Any]] = []
    for ticker in favorable:
        if ticker in unfavorable:
            continue
        weight = float(weights.get(ticker, 0.0))
        rows.append(
            {
                "Ticker": ticker,
                "Peso actual": weight,
                "Peso actual %": weight * 100.0,
                "Consistencia con portafolio": "Alta" if weight > 0 else "Fuera del portafolio",
                "Razon": (
                    "Ticker con señal favorable y sin contradicción directa en la lectura táctica."
                ),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=["Ticker", "Peso actual", "Peso actual %", "Consistencia con portafolio", "Razon"]
        )

    df = pd.DataFrame(rows).sort_values(by=["Peso actual", "Ticker"], ascending=[False, True]).reset_index(drop=True)
    return df


def portfolio_metrics(
    portfolio_returns: pd.Series,
    var_cvar_results: dict[str, Any],
) -> dict[str, Any]:
    s = _to_series(portfolio_returns, "portfolio_returns")
    if s.empty:
        return {
            "return_total": np.nan,
            "return_ann": np.nan,
            "vol_daily": np.nan,
            "vol_ann": np.nan,
            "sharpe_like": np.nan,
            "var": np.nan,
            "cvar": np.nan,
        }

    total_return = float((1.0 + s).prod() - 1.0)
    mean_daily = float(s.mean())
    vol_daily = float(s.std(ddof=1)) if len(s) > 1 else 0.0
    return_ann = float((1.0 + mean_daily) ** 252 - 1.0)
    vol_ann = float(vol_daily * np.sqrt(252))
    sharpe_like = float((mean_daily * 252) / vol_ann) if vol_ann > 0 else np.nan

    var_value = _first_numeric(var_cvar_results, ["var", "VaR", "portfolio_var", "var_95"], default=np.nan)
    cvar_value = _first_numeric(var_cvar_results, ["cvar", "CVaR", "portfolio_cvar", "cvar_95"], default=np.nan)

    return {
        "return_total": total_return,
        "return_ann": return_ann,
        "vol_daily": vol_daily,
        "vol_ann": vol_ann,
        "sharpe_like": sharpe_like,
        "var": var_value,
        "cvar": cvar_value,
    }


# ============================================================
#  CLASIFICACIÓN DE RIESGO OBJETIVO
# ============================================================

def _bucket_vol_ann(x: float) -> int:
    if np.isnan(x):
        return 2
    if x <= 0.12:
        return 1
    if x <= 0.22:
        return 2
    if x <= 0.32:
        return 3
    return 4


def _bucket_var(x: float) -> int:
    if np.isnan(x):
        return 2
    if x <= 0.012:
        return 1
    if x <= 0.025:
        return 2
    if x <= 0.040:
        return 3
    return 4


def _bucket_cvar(x: float) -> int:
    if np.isnan(x):
        return 2
    if x <= 0.018:
        return 1
    if x <= 0.032:
        return 2
    if x <= 0.050:
        return 3
    return 4


def classify_objective_risk(metrics: dict[str, Any]) -> dict[str, Any]:
    vol_score = _bucket_vol_ann(float(metrics.get("vol_ann", np.nan)))
    var_score = _bucket_var(float(metrics.get("var", np.nan)))
    cvar_score = _bucket_cvar(float(metrics.get("cvar", np.nan)))

    component_scores = [vol_score, var_score, cvar_score]
    avg_score = float(np.mean(component_scores))
    max_score = int(max(component_scores))

    if max_score == 4 and avg_score >= 3.3:
        final_score = 4
    elif avg_score >= 2.75:
        final_score = 3
    elif avg_score >= 1.75:
        final_score = 2
    else:
        final_score = 1

    reasons: list[str] = []
    reasons.append(f"Volatilidad anualizada: {metrics.get('vol_ann', np.nan):.2%}")
    reasons.append(f"VaR histórico: {metrics.get('var', np.nan):.2%}")
    reasons.append(f"CVaR histórico: {metrics.get('cvar', np.nan):.2%}")

    return {
        "risk_score": final_score,
        "risk_label": RISK_LABELS[final_score],
        "component_scores": {
            "volatility": vol_score,
            "var": var_score,
            "cvar": cvar_score,
        },
        "risk_points": RISK_SCORE_TO_POINTS[final_score],
        "rationale": (
            "El riesgo objetivo se clasifica exclusivamente con métricas del portafolio "
            "y no depende del perfil del inversor. " + " | ".join(reasons)
        ),
    }


# ============================================================
#  PERFIL Y REGLA FINAL DE DECISIÓN
# ============================================================

def resolve_profile(profile_name: str, custom_profile: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    profile_key = str(profile_name or "balanceado").strip().lower()

    if profile_key == "personalizado":
        config = {**DEFAULT_CUSTOM_PROFILE, **(custom_profile or {})}
        return config

    if profile_key not in PROFILE_CATALOG:
        profile_key = "balanceado"

    return PROFILE_CATALOG[profile_key].copy()


def build_base_score(
    objective_risk: dict[str, Any],
    signal_summary: dict[str, Any],
    benchmark_summary: dict[str, Any],
) -> dict[str, Any]:
    risk_points = float(objective_risk.get("risk_points", 50.0))
    signals_score = float(signal_summary.get("score", 50.0))
    benchmark_score = float(benchmark_summary.get("score", 50.0))

    base_score = (
        0.45 * risk_points
        + 0.35 * signals_score
        + 0.20 * benchmark_score
    )

    return {
        "risk_points": risk_points,
        "signals_score": signals_score,
        "benchmark_score": benchmark_score,
        "base_score": float(np.clip(base_score, 0.0, 100.0)),
    }


def build_final_decision(
    objective_risk: dict[str, Any],
    profile_info: dict[str, Any],
    signal_summary: dict[str, Any],
    benchmark_summary: dict[str, Any],
    score_bundle: dict[str, Any],
    selective_buys_df: pd.DataFrame,
) -> dict[str, Any]:
    risk_score = int(objective_risk["risk_score"])
    risk_label = objective_risk["risk_label"]

    base_score = float(score_bundle["base_score"])
    favorable_ratio = float(signal_summary.get("favorable_ratio", 0.0))
    benchmark_tone = str(benchmark_summary.get("tone", "neutral"))

    max_risk_for_buy = int(profile_info["max_risk_for_buy"])
    buy_threshold = float(profile_info["buy_threshold"])
    hold_threshold = float(profile_info["hold_threshold"])
    min_favorable_ratio = float(profile_info["min_favorable_ratio"])
    require_non_negative_benchmark = bool(profile_info["require_non_negative_benchmark"])
    allow_tactical_buy_on_high_risk = bool(profile_info["allow_tactical_buy_on_high_risk"])

    benchmark_ok = (benchmark_tone != "negative") if require_non_negative_benchmark else True
    signals_ok = favorable_ratio >= min_favorable_ratio
    has_selective_candidates = not selective_buys_df.empty

    stance = "Mantener"
    action = "Mantener y monitorear"
    explanation = []

    # Regla: el perfil no toca el riesgo medido, solo la decisión final
    if risk_score <= max_risk_for_buy and base_score >= buy_threshold and signals_ok and benchmark_ok and has_selective_candidates:
        stance = "Compra selectiva"
        action = "Incrementar exposición de forma selectiva"
        explanation.append(
            "El perfil elegido permite compra porque el riesgo objetivo del portafolio "
            "está dentro del rango aceptado para este perfil."
        )
        explanation.append(
            "La señal agregada del portafolio y los candidatos favorables justifican una compra selectiva."
        )

    elif (
        risk_score == 3
        and allow_tactical_buy_on_high_risk
        and base_score >= buy_threshold
        and has_selective_candidates
    ):
        stance = "Compra táctica"
        action = "Tomar exposición táctica controlada"
        explanation.append(
            "Aunque el riesgo objetivo es alto, el perfil agresivo permite una compra táctica "
            "si el puntaje base y las señales son suficientemente fuertes."
        )

    elif base_score >= hold_threshold:
        stance = "Mantener / vigilar"
        action = "Mantener posición y revisar rebalanceo"
        explanation.append(
            "El portafolio no cumple la regla de compra del perfil, "
            "pero tampoco exige reducción inmediata."
        )

    else:
        stance = "Reducir / esperar"
        action = "Esperar mejor punto o recortar exposición"
        explanation.append(
            "La combinación de riesgo objetivo, señales y/o benchmark no supera "
            "el umbral mínimo de permanencia recomendado para este perfil."
        )

    explanation.append(
        f"Riesgo objetivo: {risk_label}. "
        f"Puntaje base: {base_score:.1f}. "
        f"Perfil aplicado: {profile_info['nombre']}."
    )

    return {
        "stance": stance,
        "action": action,
        "base_score": base_score,
        "explanation": " ".join(explanation),
        "profile_effect": profile_info["que_modifica"],
    }


# ============================================================
#  TABLAS PARA LA UI
# ============================================================

def build_weights_df(weights: pd.Series) -> pd.DataFrame:
    df = weights.rename("Peso").reset_index()
    df.columns = ["Ticker", "Peso"]
    df["Peso %"] = df["Peso"] * 100.0
    df = df.sort_values(by="Peso", ascending=False).reset_index(drop=True)
    return df


def build_metrics_df(metrics: dict[str, Any], confidence_level: float) -> pd.DataFrame:
    rows = [
        {"Metrica": "Retorno total", "Valor": metrics.get("return_total", np.nan)},
        {"Metrica": "Retorno anualizado", "Valor": metrics.get("return_ann", np.nan)},
        {"Metrica": "Volatilidad diaria", "Valor": metrics.get("vol_daily", np.nan)},
        {"Metrica": "Volatilidad anualizada", "Valor": metrics.get("vol_ann", np.nan)},
        {"Metrica": f"VaR ({confidence_level:.0%})", "Valor": metrics.get("var", np.nan)},
        {"Metrica": f"CVaR ({confidence_level:.0%})", "Valor": metrics.get("cvar", np.nan)},
        {"Metrica": "Sharpe-like", "Valor": metrics.get("sharpe_like", np.nan)},
    ]
    return pd.DataFrame(rows)


def build_scorecard_df(
    objective_risk: dict[str, Any],
    signal_summary: dict[str, Any],
    benchmark_summary: dict[str, Any],
    score_bundle: dict[str, Any],
) -> pd.DataFrame:
    rows = [
        {
            "Dimension": "Riesgo objetivo",
            "Etiqueta": objective_risk["risk_label"],
            "Puntaje": score_bundle["risk_points"],
            "Detalle": objective_risk["rationale"],
        },
        {
            "Dimension": "Señales",
            "Etiqueta": signal_summary.get("tone", "neutral"),
            "Puntaje": score_bundle["signals_score"],
            "Detalle": signal_summary.get("summary_text", ""),
        },
        {
            "Dimension": "Benchmark",
            "Etiqueta": benchmark_summary.get("tone", "neutral"),
            "Puntaje": score_bundle["benchmark_score"],
            "Detalle": benchmark_summary.get("summary_text", ""),
        },
        {
            "Dimension": "Puntaje base",
            "Etiqueta": "Agregado",
            "Puntaje": score_bundle["base_score"],
            "Detalle": (
                "Este puntaje es objetivo y común a todos los perfiles. "
                "El perfil solo cambia la regla de decisión final."
            ),
        },
    ]
    return pd.DataFrame(rows)


# ============================================================
#  MOTOR PRINCIPAL
# ============================================================

def run_decision_engine(
    inputs: DecisionEngineInputs,
    deps: Optional[EngineDependencies] = None,
) -> DecisionEngineResult:
    deps = deps or EngineDependencies()
    warnings: list[str] = []

    tickers = _clean_tickers(inputs.tickers)
    if not tickers:
        raise ValueError("Debes enviar al menos un ticker al decision engine.")

    # 1) Datos base del portafolio
    _, returns_frame = _coerce_price_or_return_frame(
        tickers=tickers,
        prices_df=inputs.prices_df,
        returns_df=inputs.returns_df,
    )

    # 2) Pesos
    mode = str(inputs.weighting_mode or "equal").strip().lower()
    markowitz_weights = inputs.markowitz_weights

    if mode == "markowitz" and markowitz_weights is None and deps.markowitz_func is not None:
        try:
            generated = deps.markowitz_func(
                tickers=tickers,
                prices_df=inputs.prices_df,
                returns_df=returns_frame,
            )
            markowitz_weights = generated
        except Exception as exc:
            warnings.append(f"No fue posible obtener pesos de Markowitz: {exc}")

    weights = build_portfolio_weights(
        tickers=tickers,
        mode=mode,
        manual_weights=inputs.manual_weights,
        markowitz_weights=markowitz_weights,
    )

    # 3) Retornos del portafolio
    portfolio_returns = compute_portfolio_returns(returns_frame, weights)

    # 4) VaR / CVaR
    if inputs.var_cvar_results is not None:
        var_cvar_results = inputs.var_cvar_results
    elif deps.var_cvar_func is not None:
        try:
            var_cvar_results = deps.var_cvar_func(portfolio_returns, inputs.confidence_level)
        except Exception as exc:
            warnings.append(f"Fallo integración VaR/CVaR. Se usa cálculo histórico interno: {exc}")
            var_cvar_results = historical_var_cvar(portfolio_returns, inputs.confidence_level)
    else:
        var_cvar_results = historical_var_cvar(portfolio_returns, inputs.confidence_level)

    # 5) GARCH
    if inputs.garch_results is not None:
        garch_results = inputs.garch_results
    elif deps.garch_func is not None:
        try:
            garch_results = deps.garch_func(portfolio_returns)
        except Exception as exc:
            warnings.append(f"Fallo integración GARCH: {exc}")
            garch_results = {}
    else:
        garch_results = {}

    # 6) Benchmark
    if inputs.benchmark_summary is not None:
        benchmark_summary = inputs.benchmark_summary
    elif deps.benchmark_func is not None:
        try:
            benchmark_summary = deps.benchmark_func(portfolio_returns, inputs.benchmark_returns)
        except Exception as exc:
            warnings.append(f"Fallo integración benchmark. Se usa resumen interno: {exc}")
            benchmark_summary = default_benchmark_summary(portfolio_returns, inputs.benchmark_returns)
    else:
        benchmark_summary = default_benchmark_summary(portfolio_returns, inputs.benchmark_returns)

    # 7) Señales
    if inputs.signal_summary is not None:
        raw_signal_summary = inputs.signal_summary
    elif deps.signals_func is not None and inputs.prices_df is not None:
        try:
            raw_signal_summary = deps.signals_func(inputs.prices_df, tickers)
        except Exception as exc:
            warnings.append(f"Fallo integración de señales: {exc}")
            raw_signal_summary = {}
    else:
        raw_signal_summary = {}

    signal_summary = summarize_signals(raw_signal_summary, tickers, weights)

    # 8) Métricas y riesgo objetivo
    metrics = portfolio_metrics(portfolio_returns, var_cvar_results)
    objective_risk = classify_objective_risk(metrics)

    # 9) Perfil
    profile_info = resolve_profile(inputs.investor_profile, inputs.custom_profile)

    # 10) Compras selectivas
    selective_buys_df = build_selective_buys(signal_summary, weights)

    # 11) Puntaje base + decisión final
    score_bundle = build_base_score(
        objective_risk=objective_risk,
        signal_summary=signal_summary,
        benchmark_summary=benchmark_summary,
    )

    final_decision = build_final_decision(
        objective_risk=objective_risk,
        profile_info=profile_info,
        signal_summary=signal_summary,
        benchmark_summary=benchmark_summary,
        score_bundle=score_bundle,
        selective_buys_df=selective_buys_df,
    )

    # 12) Tablas para UI
    weights_df = build_weights_df(weights)
    metrics_df = build_metrics_df(metrics, inputs.confidence_level)
    scorecard_df = build_scorecard_df(
        objective_risk=objective_risk,
        signal_summary=signal_summary,
        benchmark_summary=benchmark_summary,
        score_bundle=score_bundle,
    )

    return DecisionEngineResult(
        weights=weights,
        portfolio_returns=portfolio_returns,
        weights_df=weights_df,
        metrics_df=metrics_df,
        scorecard_df=scorecard_df,
        selective_buys_df=selective_buys_df,
        objective_risk=objective_risk,
        profile_info=profile_info,
        signal_summary=signal_summary,
        benchmark_summary=benchmark_summary,
        garch_results=garch_results,
        final_decision=final_decision,
        warnings=warnings,
    )