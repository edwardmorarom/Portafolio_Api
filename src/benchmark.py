from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import TRADING_DAYS
from src.capm import jensen_alpha


def cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    Retorno acumulado tipo wealth index.
    """
    if returns.empty:
        return returns
    return (1 + returns).cumprod()


def max_drawdown(cum_returns: pd.Series) -> float:
    """
    Máximo drawdown.
    """
    if cum_returns.empty:
        return np.nan
    running_max = cum_returns.cummax()
    drawdown = cum_returns / running_max - 1
    return float(drawdown.min())


def sharpe_ratio(returns: pd.Series, rf_annual: float) -> float:
    if returns.empty:
        return np.nan
    annual_return = returns.mean() * TRADING_DAYS
    annual_vol = returns.std(ddof=1) * np.sqrt(TRADING_DAYS)
    if annual_vol == 0:
        return np.nan
    return float((annual_return - rf_annual) / annual_vol)


def tracking_error(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    df = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    if df.empty:
        return np.nan
    active = df.iloc[:, 0] - df.iloc[:, 1]
    return float(active.std(ddof=1) * np.sqrt(TRADING_DAYS))


def information_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    df = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    if df.empty:
        return np.nan
    active = df.iloc[:, 0] - df.iloc[:, 1]
    te = active.std(ddof=1) * np.sqrt(TRADING_DAYS)
    if te == 0:
        return np.nan
    return float((active.mean() * TRADING_DAYS) / te)


def benchmark_summary(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    rf_annual: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Tabla resumen portafolio vs benchmark.
    """
    df = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    if df.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.Series(dtype=float),
            pd.Series(dtype=float),
        )

    df.columns = ["portfolio", "benchmark"]

    cum_port = cumulative_returns(df["portfolio"])
    cum_bench = cumulative_returns(df["benchmark"])

    rows = [
        {
            "serie": "Portafolio",
            "ret_acumulado": cum_port.iloc[-1] - 1,
            "ret_anualizado": df["portfolio"].mean() * TRADING_DAYS,
            "vol_anualizada": df["portfolio"].std(ddof=1) * np.sqrt(TRADING_DAYS),
            "sharpe": sharpe_ratio(df["portfolio"], rf_annual),
            "max_drawdown": max_drawdown(cum_port),
        },
        {
            "serie": "Benchmark",
            "ret_acumulado": cum_bench.iloc[-1] - 1,
            "ret_anualizado": df["benchmark"].mean() * TRADING_DAYS,
            "vol_anualizada": df["benchmark"].std(ddof=1) * np.sqrt(TRADING_DAYS),
            "sharpe": sharpe_ratio(df["benchmark"], rf_annual),
            "max_drawdown": max_drawdown(cum_bench),
        },
    ]

    summary = pd.DataFrame(rows)
    alpha = jensen_alpha(df["portfolio"], df["benchmark"], rf_annual)
    te = tracking_error(df["portfolio"], df["benchmark"])
    ir = information_ratio(df["portfolio"], df["benchmark"])

    extras = pd.DataFrame(
        {
            "métrica": ["Alpha de Jensen", "Tracking Error", "Information Ratio"],
            "valor": [alpha, te, ir],
        }
    )

    extras["valor"] = pd.to_numeric(extras["valor"], errors="coerce")

    return summary, extras, cum_port, cum_bench