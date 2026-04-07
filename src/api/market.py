from __future__ import annotations

import logging
from typing import List, Dict

import pandas as pd
import yfinance as yf
import streamlit as st

logger = logging.getLogger(__name__)


def _standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza columnas OHLCV descargadas por yfinance.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    # Manejo de MultiIndex
    if isinstance(out.columns, pd.MultiIndex):
        level0 = out.columns.get_level_values(0)
        level1 = out.columns.get_level_values(1)

        expected = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}

        if set(level0).intersection(expected):
            out.columns = level0
        elif set(level1).intersection(expected):
            out.columns = level1
        else:
            out.columns = ["_".join(map(str, c)).strip() for c in out.columns.to_flat_index()]

    cols = {str(c).lower(): c for c in out.columns}
    rename_map = {}

    for desired in ["open", "high", "low", "close", "adj close", "volume"]:
        if desired in cols:
            rename_map[cols[desired]] = desired.title() if desired != "adj close" else "Adj Close"

    out = out.rename(columns=rename_map).copy()

    keep_cols = [c for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in out.columns]
    if keep_cols:
        out = out[keep_cols]

    out.index = pd.to_datetime(out.index)
    out = out.sort_index()
    out = out[~out.index.duplicated(keep="last")]

    return out


def _validate_ohlcv(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Valida que los datos tengan estructura mínima correcta.
    """
    if df is None or df.empty:
        raise ValueError(f"[API ERROR] {ticker}: datos vacíos")

    valid_price_cols = {"Close", "Adj Close"}

    if not valid_price_cols.intersection(set(df.columns)):
        raise ValueError(
            f"[API ERROR] {ticker}: no tiene columnas de precio válidas. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    return df


@st.cache_data(show_spinner=False, ttl=3600)
def get_prices(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Descarga datos de mercado desde Yahoo Finance con limpieza y validación.
    """
    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            actions=False,
            threads=False,
        )

        df = _standardize_ohlcv(df)
        df = _validate_ohlcv(df, ticker)

        return df

    except Exception as e:
        logger.error(f"[YFINANCE ERROR] {ticker}: {e}")
        raise RuntimeError(f"No se pudo descargar datos para {ticker}")


def get_multiple_prices(tickers: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    """
    Descarga múltiples activos sin romper el sistema si uno falla.
    """
    data = {}

    for ticker in tickers:
        try:
            data[ticker] = get_prices(ticker, start, end)
        except Exception as e:
            logger.warning(f"[WARNING] {ticker} falló: {e}")
            data[ticker] = pd.DataFrame()

    return data