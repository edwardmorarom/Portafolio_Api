import streamlit as st
import pandas as pd

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
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    get_ticker,
    get_local_benchmark,
    ensure_project_dirs,
)
from src.download import download_single_ticker
from src.returns_analysis import compute_return_series
from src.capm import compute_beta_and_capm
from src.api.macro import macro_snapshot
from src.plots import plot_scatter_regression

ensure_project_dirs()


def style_plot(fig, modo: str):
    font_color = "#6B7280" if modo == "Estadístico" else "#334155"
    grid_color = "rgba(148, 163, 184, 0.16)"
    legend_font = "#334155" if modo == "General" else "#5B2132"
    axis_title = "#0F172A"
    tick_color = "#475569"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            bordercolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(color=legend_font, size=11),
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        hoverlabel=dict(font_size=12, bgcolor="#FFFFFF", font_color="#0F172A"),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(color=tick_color),
        title_font=dict(color=axis_title),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(color=tick_color),
        title_font=dict(color=axis_title),
    )
    return fig


def interpret_capm(beta, alpha_diaria, r_squared, expected_return, rf_annual):
    parts = []

    if beta is not None:
        if beta > 1:
            parts.append(f"La beta de {beta:.4f} sugiere que el activo es más sensible que el mercado")
        elif beta < 1:
            parts.append(f"La beta de {beta:.4f} indica un perfil más defensivo que el benchmark")
        else:
            parts.append(f"La beta de {beta:.4f} sugiere sensibilidad similar a la del mercado")

    if alpha_diaria is not None:
        parts.append(f"el alpha diario estimado es {alpha_diaria:.6f}")

    if r_squared is not None:
        parts.append(f"y el R² del ajuste es {r_squared:.4f}")

    if expected_return is not None:
        parts.append(
            f". Bajo CAPM, el retorno esperado anual es {expected_return:.2%}, frente a una tasa libre de riesgo de {rf_annual:.2%}"
        )

    text = ", ".join(parts).replace(", .", ". ").strip()
    if not text:
        return "No fue posible construir una interpretación automática del ajuste CAPM."
    return text + "." if not text.endswith(".") else text


def interpret_scatter():
    return "La nube de puntos muestra cómo se relacionan los excesos de retorno del activo y del benchmark. La pendiente de la recta resume la beta, mientras que la dispersión alrededor refleja riesgo idiosincrático."


def classification_note(classification):
    if not classification:
        return "No fue posible clasificar el activo frente al benchmark."
    return f"La clasificación obtenida es: {classification}. Esta etiqueta resume si el activo se comporta de forma más agresiva, defensiva o cercana al mercado."


# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros CAPM",
    filtros_expanded=False,
)

# ==============================
# SIDEBAR
# ==============================
with filtros_sidebar:
    asset_name = st.selectbox("Activo", list(ASSETS.keys()), index=0, key="capm_asset")

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
        key="capm_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="capm_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="capm_end")

    mostrar_tabla = st.checkbox("Mostrar tabla técnica", value=False, key="capm_show_table")
    mostrar_interpretacion_tecnica = False
    if modo == "Estadístico":
        mostrar_interpretacion_tecnica = st.checkbox(
            "Mostrar interpretación técnica",
            value=True,
            key="capm_show_tech_interp"
        )

# ==============================
# DATOS
# ==============================
ticker = get_ticker(asset_name)
benchmark_ticker = get_local_benchmark(asset_name)

asset_df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))
bench_df = download_single_ticker(ticker=benchmark_ticker, start=str(start_date), end=str(end_date))

if asset_df.empty or bench_df.empty:
    st.error("No se pudieron descargar los datos del activo o del benchmark.")
    st.stop()

asset_price = asset_df["Adj Close"] if "Adj Close" in asset_df.columns else asset_df["Close"]
bench_price = bench_df["Adj Close"] if "Adj Close" in bench_df.columns else bench_df["Close"]

asset_ret = compute_return_series(asset_price)["simple_return"]
bench_ret = compute_return_series(bench_price)["simple_return"]

macro = macro_snapshot()
rf_annual = (
    macro["risk_free_rate_pct"] / 100
    if macro["risk_free_rate_pct"] == macro["risk_free_rate_pct"]
    else 0.03
)

res = compute_beta_and_capm(asset_ret, bench_ret, rf_annual=rf_annual)

if not res:
    st.warning("No hay suficientes datos alineados para CAPM.")
    st.stop()

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 4 - CAPM y Beta",
    "Evalúa sensibilidad al mercado, rendimiento esperado y riesgo sistemático del activo",
    modo=modo,
)

if modo == "General":
    nota("Este módulo muestra qué tan sensible es el activo frente al benchmark y cómo se estima su retorno esperado bajo CAPM.")
else:
    nota("En modo estadístico se enfatiza la beta como medida de riesgo sistemático, el alpha, el ajuste de regresión y la lectura económica del CAPM.")

# ==============================
# RESUMEN
# ==============================
seccion("Resumen Del Módulo")

if modo == "General":
    nota(
        f"Se compara {asset_name} ({ticker}) con su benchmark local {benchmark_ticker} entre {start_date} y {end_date} para medir sensibilidad al mercado y retorno esperado."
    )
else:
    nota(
        f"Se estima beta, alpha diario, R² y retorno esperado CAPM para {asset_name} ({ticker}) frente al benchmark {benchmark_ticker} en el periodo analizado."
    )

# ==============================
# KPIs
# ==============================
seccion("KPIs CAPM")

beta = res.get("beta")
alpha_diaria = res.get("alpha_diaria")
r_squared = res.get("r_squared")
expected_return = res.get("expected_return_capm_annual")
classification = res.get("classification")

beta_delta = ""
if beta is not None:
    if beta > 1:
        beta_delta = "Más sensible que el mercado"
    elif beta < 1:
        beta_delta = "Más defensivo que el mercado"
    else:
        beta_delta = "Sensibilidad similar al mercado"

alpha_delta = ""
if alpha_diaria is not None:
    if alpha_diaria > 0:
        alpha_delta = "Alpha positivo"
    elif alpha_diaria < 0:
        alpha_delta = "Alpha negativo"

r2_delta = ""
if r_squared is not None:
    if r_squared >= 0.60:
        r2_delta = "Buen ajuste"
    elif r_squared >= 0.30:
        r2_delta = "Ajuste moderado"
    else:
        r2_delta = "Ajuste bajo"

ret_delta = ""
if expected_return is not None:
    if expected_return > rf_annual:
        ret_delta = "Sobre tasa libre de riesgo"
    elif expected_return < rf_annual:
        ret_delta = "Bajo tasa libre de riesgo"

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Beta",
        f"{beta:.4f}" if beta is not None else "N/D",
        beta_delta,
        help_text="Pendiente de la regresión del activo frente al benchmark.",
        subtexto="Sensibilidad sistemática frente al mercado.",
    )

with c2:
    tarjeta_kpi(
        "Alpha diaria",
        f"{alpha_diaria:.6f}" if alpha_diaria is not None else "N/D",
        alpha_delta,
        help_text="Componente del rendimiento no explicado por el mercado.",
        subtexto="Exceso de retorno no explicado por la beta.",
    )

with c3:
    tarjeta_kpi(
        "R²",
        f"{r_squared:.4f}" if r_squared is not None else "N/D",
        r2_delta,
        help_text="Proporción de la variación explicada por la regresión CAPM.",
        subtexto="Capacidad explicativa del ajuste lineal.",
    )

with c4:
    tarjeta_kpi(
        "Retorno esperado anual",
        f"{expected_return:.2%}" if expected_return is not None else "N/D",
        ret_delta,
        help_text="Rendimiento esperado anual bajo CAPM.",
        subtexto="Retorno teórico compatible con el riesgo sistemático.",
    )

plot_card_footer(interpret_capm(beta, alpha_diaria, r_squared, expected_return, rf_annual))

# ==============================
# CLASIFICACIÓN
# ==============================
seccion("Clasificación Del Activo")
nota(classification_note(classification))

# ==============================
# TABLA TÉCNICA
# ==============================
summary_df = pd.DataFrame(
    {
        "metric": [
            "beta",
            "alpha_diaria",
            "r_squared",
            "p_value_beta",
            "expected_return_capm_annual",
            "classification",
        ],
        "value": [
            res["beta"],
            res["alpha_diaria"],
            res["r_squared"],
            res["p_value_beta"],
            res["expected_return_capm_annual"],
            res["classification"],
        ],
    }
)
summary_df["value"] = summary_df["value"].astype(str)

seccion("Resumen Técnico")

if mostrar_tabla:
    st.dataframe(summary_df, use_container_width=True)
else:
    with st.expander("Ver tabla técnica completa"):
        st.dataframe(summary_df, use_container_width=True)

# ==============================
# GRÁFICO
# ==============================
seccion("Regresión CAPM")

plot_card_header(
    "Relación activo-mercado",
    "El diagrama de dispersión muestra cómo responde el activo a los movimientos del benchmark y permite interpretar visualmente la beta.",
    modo=modo,
    caption="Usa los filtros para limpiar la lectura o enfatizar la recta de regresión.",
)

toolbar_label("Capas del gráfico")
cg1, cg2, cg3 = st.columns(3)
with cg1:
    show_points = st.checkbox("Puntos", value=True, key="capm_show_points")
with cg2:
    show_line = st.checkbox("Recta CAPM", value=True, key="capm_show_line")
with cg3:
    clean_view = st.checkbox("Vista limpia", value=False, key="capm_clean_view")

fig = plot_scatter_regression(
    x=res["scatter_data"]["market_excess"],
    y=res["scatter_data"]["asset_excess"],
    yhat=res["regression_line"]["y"],
    title="Regresión CAPM",
)
fig = style_plot(fig, modo)

fig.update_layout(
    title=dict(
        text="Regresión CAPM",
        x=0.03,
        xanchor="left",
        y=0.97,
        yanchor="top",
    ),
    margin=dict(l=20, r=20, t=70, b=20),
)

for trace in fig.data:
    trace_name = str(getattr(trace, "name", "") or "").lower()

    if any(k in trace_name for k in ["scatter", "puntos", "observ", "asset", "activo"]):
        trace.visible = True if show_points else "legendonly"
        try:
            trace.marker.color = "#7DD3FC" if modo == "General" else "#F9A8D4"
            trace.marker.size = 7
            trace.opacity = 0.78
        except Exception:
            pass

    elif any(k in trace_name for k in ["regression", "recta", "line", "fit"]):
        trace.visible = True if show_line else "legendonly"
        try:
            trace.line.color = "#22C55E" if modo == "General" else "#FB7185"
            trace.line.width = 2.8
        except Exception:
            pass

if clean_view:
    try:
        fig.update_layout(showlegend=False)
    except Exception:
        pass

st.plotly_chart(fig, use_container_width=True)
plot_card_footer(interpret_scatter())

# ==============================
# INTERPRETACIÓN
# ==============================
seccion("Interpretación")

if modo == "General":
    if beta is not None:
        if beta > 1:
            nota(
                "El activo se mueve con más intensidad que el mercado. Esto implica mayor sensibilidad y, en general, mayor riesgo sistemático."
            )
        elif beta < 1:
            nota(
                "El activo se mueve con menor intensidad que el benchmark. Su perfil es relativamente más defensivo frente al riesgo sistemático."
            )
        else:
            nota(
                "El activo presenta una sensibilidad cercana a la del mercado, con una beta aproximadamente unitaria."
            )
else:
    if mostrar_interpretacion_tecnica:
        nota(
            "Beta mayor que uno implica mayor sensibilidad al mercado; beta menor que uno sugiere un perfil más defensivo. En el marco CAPM, el rendimiento esperado remunera principalmente la exposición al riesgo sistemático, mientras que el riesgo no sistemático es diversificable."
        )

# ==============================
# CONTEXTO ADICIONAL
# ==============================
if modo == "Estadístico":
    with st.expander("Ver contexto de tasa libre de riesgo"):
        st.write(f"Tasa libre de riesgo anual usada en el cálculo: **{rf_annual:.2%}**")