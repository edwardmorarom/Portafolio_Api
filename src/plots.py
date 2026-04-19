from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


ASSET_COLORS = {
    "3382.T": "#3B82F6",
    "ATD.TO": "#2563EB",
    "FEMSAUBD.MX": "#DC2626",
    "BP.L": "#16A34A",
    "CA.PA": "#F59E0B",
    "ACWI": "#0EA5E9",
    "Portafolio": "#1D4ED8",
    "Benchmark": "#475569",
}

METHOD_COLORS = {
    "Histórico": "#2563EB",
    "Paramétrico": "#F59E0B",
    "Monte Carlo": "#DC2626",
}

INDICATOR_COLORS = {
    "Close": "#1D4ED8",
    "SMA": "#0EA5E9",
    "EMA": "#F97316",
    "BB_up": "#16A34A",
    "BB_mid": "#64748B",
    "BB_low": "#DC2626",
    "RSI": "#2563EB",
    "MACD": "#1D4ED8",
    "MACD_signal": "#F97316",
    "MACD_hist": "#93C5FD",
    "%K": "#1D4ED8",
    "%D": "#F97316",
    "Forecast": "#2563EB",
    "Regresión": "#1D4ED8",
    "Observaciones": "#7DD3FC",
}


PLOT_BG = "#FFFFFF"
PLOT_PANEL = "#F8FBFF"
GRID_COLOR = "rgba(148, 163, 184, 0.22)"
TEXT_MAIN = "#0F172A"
TEXT_SOFT = "#475569"
BORDER_SOFT = "rgba(148, 163, 184, 0.24)"
HOVER_BG = "#0F172A"
HOVER_TEXT = "#F8FAFC"


def _get_asset_color(name: str) -> str:
    return ASSET_COLORS.get(name, "#3B82F6")


def _apply_layout(fig: go.Figure, title: str, xaxis_title: str = "Fecha", yaxis_title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            x=0.02,
            xanchor="left",
            font=dict(size=24, color=TEXT_MAIN),
        ),
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_PANEL,
        font=dict(color=TEXT_MAIN, size=13),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=470,
        margin=dict(l=40, r=40, t=70, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(255,255,255,0.75)",
            bordercolor=BORDER_SOFT,
            borderwidth=1,
            font=dict(size=11, color=TEXT_MAIN),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=HOVER_BG,
            bordercolor="#1D4ED8",
            font=dict(color=HOVER_TEXT),
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        tickfont=dict(color=TEXT_SOFT),
        title_font=dict(color=TEXT_MAIN),
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zeroline=False,
        showline=False,
        tickfont=dict(color=TEXT_SOFT),
        title_font=dict(color=TEXT_MAIN),
    )
    return fig


def _add_reference_line(
    fig: go.Figure,
    y: float,
    text: str = "",
    color: str = "rgba(100, 116, 139, 0.65)",
    dash: str = "dash",
):
    fig.add_hline(y=y, line_dash=dash, line_color=color)
    return fig


def plot_normalized_prices(close: pd.DataFrame) -> go.Figure:
    base = close / close.dropna().iloc[0] * 100
    fig = go.Figure()

    for col in base.columns:
        fig.add_trace(
            go.Scatter(
                x=base.index,
                y=base[col],
                mode="lines",
                name=col,
                line=dict(color=_get_asset_color(col), width=2.5),
            )
        )

    return _apply_layout(fig, "Precios Normalizados (Base 100)", "Fecha", "Base 100")


def plot_price_and_mas(df: pd.DataFrame, sma_col: str, ema_col: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Close",
            line=dict(color=INDICATOR_COLORS["Close"], width=2.7),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[sma_col],
            mode="lines",
            name=sma_col,
            line=dict(color=INDICATOR_COLORS["SMA"], width=2.2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[ema_col],
            mode="lines",
            name=ema_col,
            line=dict(color=INDICATOR_COLORS["EMA"], width=2.2),
        )
    )

    return _apply_layout(fig, "Precio Con Medias Móviles", "Fecha", "Precio")


def plot_bollinger(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Close",
            line=dict(color=INDICATOR_COLORS["Close"], width=2.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_up"],
            mode="lines",
            name="BB_up",
            line=dict(color=INDICATOR_COLORS["BB_up"], width=2, dash="dot"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_mid"],
            mode="lines",
            name="BB_mid",
            line=dict(color=INDICATOR_COLORS["BB_mid"], width=1.9),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_low"],
            mode="lines",
            name="BB_low",
            line=dict(color=INDICATOR_COLORS["BB_low"], width=2, dash="dot"),
        )
    )

    return _apply_layout(fig, "Bandas De Bollinger", "Fecha", "Precio")


def plot_rsi(df: pd.DataFrame, rsi_col: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[rsi_col],
            mode="lines",
            name=rsi_col,
            line=dict(color=INDICATOR_COLORS["RSI"], width=2.4),
        )
    )

    _add_reference_line(fig, 70)
    _add_reference_line(fig, 30)

    fig.update_yaxes(range=[0, 100])

    return _apply_layout(fig, "RSI", "Fecha", "RSI")


def plot_macd(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MACD"],
            mode="lines",
            name="MACD",
            line=dict(color=INDICATOR_COLORS["MACD"], width=2.3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MACD_signal"],
            mode="lines",
            name="MACD_signal",
            line=dict(color=INDICATOR_COLORS["MACD_signal"], width=2.1),
        )
    )
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["MACD_hist"],
            name="MACD_hist",
            marker_color=INDICATOR_COLORS["MACD_hist"],
            opacity=0.75,
        )
    )

    return _apply_layout(fig, "MACD", "Fecha", "Valor")


def plot_stochastic(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["%K"],
            mode="lines",
            name="%K",
            line=dict(color=INDICATOR_COLORS["%K"], width=2.3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["%D"],
            mode="lines",
            name="%D",
            line=dict(color=INDICATOR_COLORS["%D"], width=2.1),
        )
    )

    _add_reference_line(fig, 80)
    _add_reference_line(fig, 20)

    fig.update_yaxes(range=[0, 100])

    return _apply_layout(fig, "Oscilador Estocástico", "Fecha", "Nivel")


def plot_histogram_with_normal(returns: pd.Series) -> go.Figure:
    r = returns.dropna()
    mu, sigma = r.mean(), r.std(ddof=1)
    x = np.linspace(r.min(), r.max(), 300)
    y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=r,
            histnorm="probability density",
            name="Histograma",
            nbinsx=40,
            marker_color="#93C5FD",
            opacity=0.88,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name="Normal teórica",
            line=dict(color="#1D4ED8", width=2.4),
        )
    )

    return _apply_layout(fig, "Histograma Con Curva Normal", "Rendimiento", "Densidad")


def plot_qq(qq_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=qq_df["theoretical_quantiles"],
            y=qq_df["sample_quantiles"],
            mode="markers",
            name="Q-Q",
            marker=dict(color="#60A5FA", size=5, opacity=0.85),
        )
    )

    min_q = float(np.nanmin([qq_df["theoretical_quantiles"].min(), qq_df["sample_quantiles"].min()]))
    max_q = float(np.nanmax([qq_df["theoretical_quantiles"].max(), qq_df["sample_quantiles"].max()]))

    fig.add_trace(
        go.Scatter(
            x=[min_q, max_q],
            y=[min_q, max_q],
            mode="lines",
            name="45°",
            line=dict(color="#1D4ED8", width=2.2),
        )
    )

    return _apply_layout(fig, "Q-Q Plot", "Cuantiles Teóricos", "Cuantiles Muestrales")


def plot_box(returns: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Box(
            y=returns.dropna(),
            name="Rendimientos",
            marker_color="#60A5FA",
            line_color="#2563EB",
            boxmean=True,
        )
    )
    return _apply_layout(fig, "Boxplot De Rendimientos", "", "Rendimiento")


def plot_volatility(vol_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    palette = ["#2563EB", "#0EA5E9", "#F97316", "#16A34A", "#DC2626"]

    for i, col in enumerate(vol_df.columns):
        fig.add_trace(
            go.Scatter(
                x=vol_df.index,
                y=vol_df[col],
                mode="lines",
                name=col,
                line=dict(color=palette[i % len(palette)], width=2.3),
            )
        )

    return _apply_layout(fig, "Volatilidad Condicional Estimada", "Fecha", "Volatilidad")


def plot_forecast(forecast_df: pd.DataFrame, long_run_vol: float | None = None) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=forecast_df["horizonte"],
            y=forecast_df["volatilidad_pronosticada"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color=INDICATOR_COLORS["Forecast"], width=2.3),
            marker=dict(size=6),
        )
    )

    if long_run_vol is not None:
        fig.add_hline(
            y=long_run_vol,
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text="Volatilidad de largo plazo",
            annotation_position="top left",
        )

    return _apply_layout(fig, "Pronóstico De Volatilidad", "Horizonte", "Volatilidad")


def plot_scatter_regression(x: np.ndarray, y: np.ndarray, yhat: np.ndarray, title: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="Observaciones",
            marker=dict(color=INDICATOR_COLORS["Observaciones"], size=6, opacity=0.75),
        )
    )

    sort_idx = np.argsort(x)
    fig.add_trace(
        go.Scatter(
            x=x[sort_idx],
            y=yhat[sort_idx],
            mode="lines",
            name="Regresión",
            line=dict(color=INDICATOR_COLORS["Regresión"], width=2.4),
        )
    )

    return _apply_layout(fig, title, "Exceso Benchmark", "Exceso Activo")


def plot_var_distribution(returns: pd.Series, table: pd.DataFrame) -> go.Figure:
    r = returns.dropna()
    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=r,
            nbinsx=50,
            name="Rendimientos",
            marker_color="#93C5FD",
            opacity=0.82,
        )
    )

    for _, row in table.iterrows():
        metodo = row["método"]
        color = METHOD_COLORS.get(metodo, "#1D4ED8")

        fig.add_trace(
            go.Scatter(
                x=[-row["VaR_diario"], -row["VaR_diario"]],
                y=[0, 1],
                mode="lines",
                name=f"VaR {metodo}",
                line=dict(color=color, width=2, dash="dash"),
                yaxis="y2",
                hovertemplate=f"VaR {metodo}: %{{x:.2%}}<extra></extra>",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[-row["CVaR_diario"], -row["CVaR_diario"]],
                y=[0, 1],
                mode="lines",
                name=f"CVaR {metodo}",
                line=dict(color=color, width=2, dash="dot"),
                yaxis="y2",
                hovertemplate=f"CVaR {metodo}: %{{x:.2%}}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(
            text="Distribución De Rendimientos Con VaR Y CVaR",
            x=0.02,
            xanchor="left",
            font=dict(size=24, color=TEXT_MAIN),
        ),
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_PANEL,
        font=dict(color=TEXT_MAIN, size=13),
        xaxis_title="Rendimiento",
        yaxis_title="Frecuencia",
        yaxis2=dict(
            overlaying="y",
            side="right",
            range=[0, 1],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
        ),
        height=470,
        margin=dict(l=40, r=120, t=70, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(255,255,255,0.75)",
            bordercolor=BORDER_SOFT,
            borderwidth=1,
            font=dict(size=11, color=TEXT_MAIN),
        ),
        barmode="overlay",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=HOVER_BG,
            bordercolor="#1D4ED8",
            font=dict(color=HOVER_TEXT),
        ),
    )

    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color=TEXT_SOFT), title_font=dict(color=TEXT_MAIN))
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, tickfont=dict(color=TEXT_SOFT), title_font=dict(color=TEXT_MAIN))

    return fig


def plot_correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Matriz De Correlación",
    )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_PANEL,
        font=dict(color=TEXT_MAIN, size=13),
        title=dict(font=dict(color=TEXT_MAIN, size=24), x=0.02),
        height=420,
        margin=dict(l=40, r=40, t=60, b=40),
        coloraxis_colorbar=dict(
            title="Correlación",
            x=1.02,
            y=0.5,
            len=0.8,
            thickness=14,
        ),
    )

    fig.update_xaxes(showgrid=False, tickfont=dict(color=TEXT_SOFT))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TEXT_SOFT))

    return fig


def plot_frontier(
    sim_df: pd.DataFrame,
    frontier_df: pd.DataFrame,
    min_var: pd.Series,
    max_sharpe: pd.Series,
) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=sim_df["volatility"],
            y=sim_df["return"],
            mode="markers",
            marker=dict(
                size=4,
                color=sim_df["sharpe"],
                colorscale="Blues",
                showscale=True,
                colorbar=dict(
                    title="Sharpe",
                    x=1.12,
                    y=0.5,
                    len=0.75,
                    thickness=16,
                ),
                opacity=0.75,
            ),
            name="Portafolios",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=frontier_df["volatility"],
            y=frontier_df["return"],
            mode="lines",
            name="Frontera eficiente",
            line=dict(color="#1D4ED8", width=3),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[min_var["volatility"]],
            y=[min_var["return"]],
            mode="markers",
            marker=dict(size=12, symbol="diamond", color="#F97316"),
            name="Mínima varianza",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[max_sharpe["volatility"]],
            y=[max_sharpe["return"]],
            mode="markers",
            marker=dict(size=14, symbol="star", color="#DC2626"),
            name="Máximo Sharpe",
        )
    )

    return _apply_layout(fig, "Frontera Eficiente De Markowitz", "Volatilidad", "Retorno")


def plot_benchmark_base100(port: pd.Series, bench: pd.Series) -> go.Figure:
    df = pd.concat([port, bench], axis=1).dropna()
    df.columns = ["Portafolio", "Benchmark"]
    base = df / df.iloc[0] * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=base.index,
            y=base["Portafolio"],
            mode="lines",
            name="Portafolio",
            line=dict(color=ASSET_COLORS["Portafolio"], width=2.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=base.index,
            y=base["Benchmark"],
            mode="lines",
            name="Benchmark",
            line=dict(color=ASSET_COLORS["Benchmark"], width=2.5),
        )
    )

    return _apply_layout(fig, "Portafolio Vs Benchmark (Base 100)", "Fecha", "Base 100")