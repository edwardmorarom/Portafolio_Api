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

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, get_ticker, ensure_project_dirs
from src.download import download_single_ticker
from src.returns_analysis import (
    compute_return_series,
    descriptive_stats,
    normality_tests,
    qq_plot_data,
    stylized_facts_comment,
)
from src.plots import plot_histogram_with_normal, plot_qq, plot_box

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
        margin=dict(l=20, r=20, t=40, b=20),
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


def interpret_distribution(mean_ret, vol_ret, min_ret, max_ret):
    return (
        f"La serie presenta un rendimiento promedio de {mean_ret:.4%}, "
        f"volatilidad de {vol_ret:.4%}, un mínimo de {min_ret:.4%} "
        f"y un máximo de {max_ret:.4%} en el periodo analizado."
    )


def interpret_histogram(modo: str):
    if modo == "General":
        return "Observa si la distribución se concentra cerca de cero o si presenta colas amplias, lo que puede indicar episodios de variación más fuerte."
    return "Contrasta la forma empírica con la referencia normal. Desviaciones visibles pueden sugerir asimetría, leptocurtosis o no normalidad."


def interpret_boxplot():
    return "El boxplot resume mediana, dispersión y valores atípicos. Una caja amplia o muchos outliers suele asociarse con mayor inestabilidad en los rendimientos."


def interpret_qq():
    return "Si los puntos se apartan de la diagonal, la distribución observada se aleja de la normalidad teórica, especialmente en colas y extremos."


# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros De Rendimientos",
    filtros_expanded=False,
)

# ==============================
# SIDEBAR
# ==============================
with filtros_sidebar:
    asset_name = st.selectbox("Activo", list(ASSETS.keys()), index=0, key="ret_asset")

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
        key="ret_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="ret_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="ret_end")

    return_type = st.radio(
        "Tipo de retorno",
        ["simple_return", "log_return"],
        index=1,
        key="ret_return_type",
    )

    mostrar_tablas = st.checkbox("Mostrar tablas completas", value=False, key="ret_show_tables")
    mostrar_qq = st.checkbox("Mostrar gráfico Q-Q", value=(modo == "Estadístico"), key="ret_show_qq")

# ==============================
# DATOS
# ==============================
ticker = get_ticker(asset_name)
df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))

if df.empty:
    st.error("No se pudieron descargar datos.")
    st.stop()

price_series = df["Adj Close"] if "Adj Close" in df.columns else df["Close"]
ret_df = compute_return_series(price_series)

if ret_df.empty or return_type not in ret_df.columns:
    st.error("No fue posible calcular la serie de rendimientos.")
    st.stop()

series = ret_df[return_type].dropna()

if series.empty:
    st.error("La serie de rendimientos está vacía.")
    st.stop()

desc_df = descriptive_stats(series)
norm_df = normality_tests(series)
qq_df = qq_plot_data(series)

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 2 - Rendimientos y propiedades empíricas",
    "Analiza la distribución de rendimientos del activo y sus principales propiedades estadísticas",
    modo=modo,
)

if modo == "General":
    nota("Este módulo resume dispersión, extremos y forma de la distribución para entender qué tan estable o irregular ha sido el activo.")
else:
    nota("En modo estadístico se enfatiza el contraste con normalidad, la lectura de colas y la detección de rasgos empíricos relevantes para medición de riesgo.")

# ==============================
# RESUMEN
# ==============================
seccion("Resumen Del Módulo")

if modo == "General":
    nota(
        f"Se analizan los rendimientos de {asset_name} ({ticker}) entre {start_date} y {end_date} "
        f"usando la serie {return_type} para evaluar comportamiento, dispersión y extremos."
    )
else:
    nota(
        f"Se estudia la serie {return_type} de {asset_name} ({ticker}) entre {start_date} y {end_date} "
        "mediante estadísticos descriptivos, pruebas de normalidad y análisis gráfico."
    )

# ==============================
# KPIs
# ==============================
seccion("KPIs De Rendimientos")

mean_ret = series.mean()
vol_ret = series.std(ddof=1)
min_ret = series.min()
max_ret = series.max()
last_ret = series.iloc[-1] if len(series) > 0 else None

prom_delta = ""
prom_sub = "Rendimiento medio del periodo."
if mean_ret > 0:
    prom_delta = "Sesgo positivo"
elif mean_ret < 0:
    prom_delta = "Sesgo negativo"

vol_delta = ""
vol_sub = "Dispersión típica de los retornos."
if vol_ret >= series.abs().median():
    vol_delta = "Alta dispersión"
else:
    vol_delta = "Dispersión moderada"

min_delta = f"Último: {last_ret:.4%}" if last_ret is not None else ""
max_delta = f"Último: {last_ret:.4%}" if last_ret is not None else ""

col1, col2, col3, col4 = st.columns(4)

with col1:
    tarjeta_kpi(
        "Promedio",
        f"{mean_ret:.4%}",
        prom_delta,
        help_text="Media de la serie de rendimientos seleccionada.",
        subtexto=prom_sub,
    )

with col2:
    tarjeta_kpi(
        "Volatilidad",
        f"{vol_ret:.4%}",
        vol_delta,
        help_text="Desviación estándar muestral de los rendimientos.",
        subtexto=vol_sub,
    )

with col3:
    tarjeta_kpi(
        "Mínimo",
        f"{min_ret:.4%}",
        min_delta,
        help_text="Peor rendimiento observado en el periodo.",
        subtexto="Extremo inferior observado.",
    )

with col4:
    tarjeta_kpi(
        "Máximo",
        f"{max_ret:.4%}",
        max_delta,
        help_text="Mejor rendimiento observado en el periodo.",
        subtexto="Extremo superior observado.",
    )

plot_card_footer(interpret_distribution(mean_ret, vol_ret, min_ret, max_ret))

# ==============================
# TABLAS
# ==============================
seccion("Resumen Estadístico")

if mostrar_tablas:
    tc1, tc2 = st.columns(2)
    with tc1:
        plot_card_header(
            "Estadísticos descriptivos",
            "Resume medidas centrales, dispersión y forma de la distribución.",
            modo=modo,
            caption="Tabla principal para revisar estructura básica de la serie.",
        )
        st.dataframe(desc_df, use_container_width=True)

    with tc2:
        plot_card_header(
            "Pruebas de normalidad",
            "Permiten contrastar si la distribución se aparta de una normal teórica.",
            modo=modo,
            caption="Revisa estadístico y p-valor para evaluar evidencia contra normalidad.",
        )
        st.dataframe(norm_df, use_container_width=True)
else:
    with st.expander("Ver tablas estadísticas"):
        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown("#### Estadísticos descriptivos")
            st.dataframe(desc_df, use_container_width=True)
        with tc2:
            st.markdown("#### Pruebas de normalidad")
            st.dataframe(norm_df, use_container_width=True)

# ==============================
# GRÁFICOS PRINCIPALES
# ==============================
seccion("Distribución De Rendimientos")

g1, g2 = st.columns(2)

with g1:
    plot_card_header(
        "Histograma con referencia normal",
        "Permite comparar la distribución observada de rendimientos contra una referencia normal teórica.",
        modo=modo,
        caption="Activa o desactiva elementos para simplificar o ampliar la lectura visual.",
    )

    toolbar_label("Capas del gráfico")
    h1, h2 = st.columns(2)
    with h1:
        show_hist = st.checkbox("Histograma", value=True, key="ret_show_hist")
    with h2:
        show_normal = st.checkbox("Curva normal", value=True, key="ret_show_normal")

    fig_hist = plot_histogram_with_normal(series)

    for trace in fig_hist.data:
        trace_name = str(getattr(trace, "name", "") or "").lower()
        if any(k in trace_name for k in ["hist", "histograma", "returns", "rendimientos"]):
            trace.visible = True if show_hist else "legendonly"
        elif any(k in trace_name for k in ["normal", "gaussian", "density", "densidad"]):
            trace.visible = True if show_normal else "legendonly"

    fig_hist = style_plot(fig_hist, modo)
    st.plotly_chart(fig_hist, use_container_width=True)
    plot_card_footer(interpret_histogram(modo))

with g2:
    plot_card_header(
        "Boxplot de rendimientos",
        "Resume mediana, rango intercuartílico y posibles valores atípicos.",
        modo=modo,
        caption="Útil para identificar rápidamente dispersión y extremos.",
    )

    toolbar_label("Opciones del gráfico")
    horizontal_box = st.checkbox("Orientación horizontal", value=False, key="ret_box_horizontal")

    fig_box = plot_box(series)

    if horizontal_box:
        try:
            fig_box.update_traces(orientation="h")
        except Exception:
            pass

    fig_box = style_plot(fig_box, modo)
    st.plotly_chart(fig_box, use_container_width=True)
    plot_card_footer(interpret_boxplot())

# ==============================
# GRÁFICO Q-Q
# ==============================
if mostrar_qq:
    seccion("Gráfico Q-Q")

    plot_card_header(
        "Contraste visual con normalidad",
        "Compara cuantiles observados con cuantiles teóricos de una normal.",
        modo=modo,
        caption="Ayuda a detectar desviaciones en colas, asimetría y no normalidad.",
    )

    toolbar_label("Opciones del gráfico")
    qq_reference = st.checkbox("Mostrar énfasis interpretativo", value=True, key="ret_qq_ref")

    fig_qq = plot_qq(qq_df)
    fig_qq = style_plot(fig_qq, modo)

    if not qq_reference:
        try:
            for trace in fig_qq.data:
                name = str(getattr(trace, "name", "") or "").lower()
                if any(k in name for k in ["line", "línea", "referencia", "45"]):
                    trace.visible = "legendonly"
        except Exception:
            pass

    st.plotly_chart(fig_qq, use_container_width=True)
    plot_card_footer(interpret_qq())

# ==============================
# INTERPRETACIÓN
# ==============================
seccion("Interpretación")

if modo == "General":
    nota(
        "Este módulo permite ver si los rendimientos han sido relativamente estables o si presentan colas y extremos "
        "que hacen más riesgosa una aproximación basada solo en normalidad."
    )
else:
    nota(stylized_facts_comment(series))

# ==============================
# DATOS RECIENTES
# ==============================
seccion("Últimos Rendimientos")

if mostrar_tablas:
    st.dataframe(ret_df.tail(15), use_container_width=True)
else:
    with st.expander("Ver últimos rendimientos"):
        st.dataframe(ret_df.tail(15), use_container_width=True)