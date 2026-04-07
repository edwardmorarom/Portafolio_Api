from __future__ import annotations

from typing import Dict, List
import pandas as pd
import streamlit as st
import yfinance as yf

from src.config import RAW_DIR, PROCESSED_DIR, ensure_project_dirs


def _standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza columnas OHLCV descargadas por yfinance.
    Soporta columnas simples y columnas MultiIndex.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    # yfinance puede devolver MultiIndex incluso para un solo ticker
    if isinstance(out.columns, pd.MultiIndex):
        level0 = out.columns.get_level_values(0)
        level1 = out.columns.get_level_values(1)

        expected = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}

        # Caso más común: nivel 0 = tipo de precio, nivel 1 = ticker
        if set(level0).intersection(expected):
            out.columns = level0

        # Respaldo: por si el orden estuviera invertido
        elif set(level1).intersection(expected):
            out.columns = level1

        else:
            # Último recurso: aplanar columnas
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


@st.cache_data(show_spinner=False, ttl=3600)
def download_single_ticker(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Descarga OHLCV de un ticker usando yfinance.
    Usa auto_adjust=False para preservar OHLC y Close crudo.
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

        if not df.empty:
            try:
                df.to_csv(RAW_DIR / f"{ticker.replace('^', '')}_raw.csv")
            except Exception:
                pass

        return df

    except Exception as e:
        print(f"Error descargando {ticker}: {e}")
        return pd.DataFrame()


from src.api.market import get_multiple_prices

@st.cache_data(show_spinner=False, ttl=3600)
def download_multiple_tickers(tickers: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    """
    Descarga múltiples tickers usando la nueva capa API.
    """
    ensure_project_dirs()

    data = get_multiple_prices(tickers=tickers, start=start, end=end)

    return data


def build_close_matrix(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Construye matriz de cierres ajustados si existen; si no, usa Close.
    """
    series = {}

    for ticker, df in data.items():
        if df.empty:
            continue

        if "Adj Close" in df.columns:
            series[ticker] = df["Adj Close"].rename(ticker)
        elif "Close" in df.columns:
            series[ticker] = df["Close"].rename(ticker)

    if not series:
        return pd.DataFrame()

    close = pd.concat(series.values(), axis=1).sort_index()
    close = close.dropna(how="all")
    return close


def build_returns_matrix(close: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula rendimientos simples diarios.
    """
    if close.empty:
        return pd.DataFrame()

    returns = close.pct_change(fill_method=None).dropna(how="all")
    return returns


@st.cache_data(show_spinner=False, ttl=3600)
def load_market_bundle(tickers: List[str], start: str, end: str) -> Dict[str, object]:
    """
    Bundle central de mercado usado en todo el dashboard.
    """
    ensure_project_dirs()
    data = download_multiple_tickers(tickers=tickers, start=start, end=end)
    close = build_close_matrix(data)
    returns = build_returns_matrix(close)

    try:
        close.to_csv(PROCESSED_DIR / "close_prices.csv")
        returns.to_csv(PROCESSED_DIR / "returns.csv")
    except Exception:
        pass

    return {
        "ohlcv": data,
        "close": close,
        "returns": returns,
    }