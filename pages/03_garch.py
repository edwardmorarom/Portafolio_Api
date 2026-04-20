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
    DEFAULT_END_DATE,
    DEFAULT_START_DATE,
    ensure_project_dirs,
    get_ticker,
)
from src.download import download_single_ticker
from src.garch_models import fit_garch_models
from src.plots import plot_forecast, plot_volatility
from src.returns_analysis import compute_return_series
from src.risk_metrics import validar_serie_para_garch

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


def interpret_validation(n_original, n_limpio, std_val):
    if n_original == 0:
        return "No hay observaciones disponibles para validar la serie."

    return (
        f"La serie parte de {n_original:,} observaciones, conserva {n_limpio:,} datos útiles "
        f"y presenta una desviación estándar de {std_val:.6f}. "
        f"Esto permite verificar si la base empírica es suficiente para un ajuste GARCH defendible."
    ).replace(",", ".")


def interpret_kpis(best_model, forecast_last, persistence, long_run_vol):
    parts = []

    if best_model is not None:
        parts.append(f"El mejor modelo seleccionado es {best_model}")

    if forecast_last is not None:
        parts.append(f"con un pronóstico final de volatilidad de {forecast_last:.4f}")

    if persistence is not None:
        parts.append(f"y una persistencia estimada de {persistence:.4f}")

    if long_run_vol is not None:
        parts.append(f". La volatilidad de largo plazo estimada es {long_run_vol:.4f}")

    text = " ".join(parts).strip()
    if not text:
        return "No fue posible construir una interpretación automática de los KPIs principales del ajuste."
    return text + "." if not text.endswith(".") else text


def interpret_volatility():
    return "La volatilidad condicional muestra cómo cambia la incertidumbre del activo a lo largo del tiempo. Picos altos suelen asociarse con episodios de tensión o choques recientes."


def interpret_forecast(mostrar_long_run: bool, long_run_vol):
    if mostrar_long_run and long_run_vol is not None:
        return (
            f"El pronóstico muestra la trayectoria esperada de la volatilidad y su convergencia hacia un nivel de largo plazo cercano a {long_run_vol:.4f}, "
            "consistente con reversión a la media bajo estacionariedad."
        )
    return "El pronóstico resume cómo evolucionaría la volatilidad hacia adelante bajo el modelo seleccionado, priorizando el impacto de choques recientes en el corto plazo."


# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros GARCH",
    filtros_expanded=False,
)

# ==============================
# SIDEBAR
# ==============================
with filtros_sidebar:
    asset_name = st.selectbox("Activo representativo", list(ASSETS.keys()), index=0, key="garch_asset")

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
        key="garch_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="garch_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="garch_end")

    mostrar_long_run = st.checkbox("Mostrar volatilidad de largo plazo", value=True, key="garch_long_run")
    mostrar_tablas = st.checkbox("Mostrar tablas completas", value=False, key="garch_show_tables")

    mostrar_diagnostico = False
    mostrar_residuos = False

    if modo == "Estadístico":
        mostrar_diagnostico = st.checkbox("Mostrar diagnóstico del modelo", value=True, key="garch_diag")
        mostrar_residuos = st.checkbox("Mostrar residuos estandarizados", value=False, key="garch_resid")

# ==============================
# DESCARGAR DATOS
# ==============================
ticker = get_ticker(asset_name)
df = download_single_ticker(ticker=ticker, start=str(start_date), end=str(end_date))

if df.empty:
    st.error("No se pudieron descargar datos.")
    st.stop()

price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
ret_df = compute_return_series(df[price_col])

if "log_return" not in ret_df.columns:
    st.error("No se encontró la columna 'log_return' para ajustar el modelo GARCH.")
    st.stop()

serie_retornos = ret_df["log_return"]

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 3 - Modelos ARCH/GARCH",
    "Analiza volatilidad condicional y pronósticos de riesgo a partir de rendimientos del activo",
    modo=modo,
)

if modo == "General":
    nota("Este módulo muestra si la volatilidad cambia a lo largo del tiempo y por qué una volatilidad fija puede ser insuficiente para medir riesgo.")
else:
    nota("En modo estadístico se enfatiza heterocedasticidad condicional, persistencia de choques y convergencia del forecast hacia volatilidad de largo plazo.")

# ==============================
# RESUMEN DEL MÓDULO
# ==============================
seccion("Resumen Del Módulo")

if modo == "General":
    nota(
        f"Se analiza {asset_name} ({ticker}) entre {start_date} y {end_date} para evaluar si la volatilidad se agrupa en episodios de calma y turbulencia."
    )
else:
    nota(
        f"Se ajustan modelos ARCH/GARCH sobre rendimientos logarítmicos de {asset_name} ({ticker}) entre {start_date} y {end_date} para modelar heterocedasticidad condicional y generar pronósticos de volatilidad."
    )

# ==============================
# VALIDACIÓN DE LA SERIE
# ==============================
validacion = validar_serie_para_garch(
    serie_retornos,
    min_obs=120,
    max_null_ratio=0.05,
)

seccion("Validación De La Serie Para GARCH")

n_original = validacion["resumen"].get("n_original", 0)
n_limpio = validacion["resumen"].get("n_limpio", 0)
std_val = validacion["resumen"].get("std", 0)

ratio_util = (n_limpio / n_original) if n_original else None

v1, v2, v3 = st.columns(3)

with v1:
    tarjeta_kpi(
        "Obs. originales",
        f"{n_original:,}".replace(",", "."),
        help_text="Cantidad total de observaciones descargadas antes del filtrado.",
        subtexto="Base inicial de datos descargados.",
    )

with v2:
    tarjeta_kpi(
        "Obs. limpias",
        f"{n_limpio:,}".replace(",", "."),
        f"{ratio_util:.1%} útiles" if ratio_util is not None else "",
        help_text="Datos válidos para estimar el modelo tras limpieza y validación.",
        subtexto="Muestra efectiva utilizable en el ajuste.",
    )

with v3:
    tarjeta_kpi(
        "Desv. estándar",
        f"{std_val:.6f}",
        help_text="Dispersión de los rendimientos logarítmicos de entrada.",
        subtexto="Volatilidad básica de la serie de entrada.",
    )

plot_card_footer(interpret_validation(n_original, n_limpio, std_val))

for adv in validacion["advertencias"]:
    st.warning(adv)

if not validacion["ok"]:
    for err in validacion["errores"]:
        st.error(err)

    nota(
        "No se ajustó el modelo GARCH porque la serie no cumple las condiciones mínimas de calidad para un ajuste defendible."
    )
    st.stop()

# ==============================
# PREPARAR DATOS PARA GARCH
# ==============================
serie_garch = validacion["serie_limpia"] * 100.0

if modo == "Estadístico":
    nota(
        "Los rendimientos logarítmicos se escalan por 100 para mejorar la estabilidad numérica del ajuste ARCH/GARCH."
    )

# ==============================
# AJUSTE DE MODELOS
# ==============================
results = fit_garch_models(serie_garch)

if results["comparison"].empty:
    st.warning("No hay suficientes datos o el ajuste no convergió correctamente para los modelos GARCH.")
    st.stop()

# ==============================
# VOLATILIDAD DE LARGO PLAZO
# ==============================
long_run_vol = None
persistence = None

try:
    best_model_name = results.get("best_model_name")
    comparison_df = results.get("comparison")

    if best_model_name is not None and comparison_df is not None and not comparison_df.empty:
        best_row = comparison_df.loc[comparison_df["modelo"] == best_model_name]

        if not best_row.empty:
            omega = pd.to_numeric(best_row["omega"], errors="coerce").iloc[0]
            alpha_1 = pd.to_numeric(best_row["alpha_1"], errors="coerce").iloc[0]

            beta_1 = None
            if "beta_1" in best_row.columns:
                beta_1 = pd.to_numeric(best_row["beta_1"], errors="coerce").iloc[0]

            if pd.notna(omega) and pd.notna(alpha_1):
                persistence = alpha_1 + beta_1 if pd.notna(beta_1) else alpha_1

                if persistence < 1:
                    long_run_var = omega / (1 - persistence)
                    if long_run_var > 0:
                        long_run_vol = long_run_var ** 0.5
except Exception:
    long_run_vol = None
    persistence = None

# ==============================
# KPIs DEL AJUSTE
# ==============================
seccion("KPIs Del Ajuste")

best_model = results.get("best_model_name", None)
n_models = len(results["comparison"]) if "comparison" in results else 0

forecast_last = None
try:
    forecast_last = float(results["forecast"]["volatilidad_pronosticada"].iloc[-1])
except Exception:
    forecast_last = None

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Activo",
        asset_name,
        help_text=f"Ticker de referencia: {ticker}",
        subtexto="Activo usado como base del ajuste.",
    )

with c2:
    tarjeta_kpi(
        "Modelos comparados",
        str(n_models),
        help_text="Número de especificaciones evaluadas en el ajuste.",
        subtexto="Cantidad de variantes ARCH/GARCH evaluadas.",
    )

with c3:
    tarjeta_kpi(
        "Mejor modelo",
        str(best_model) if best_model is not None else "N/D",
        help_text="Selección basada en criterios de comparación del ajuste.",
        subtexto="Especificación con mejor desempeño comparativo.",
    )

with c4:
    tarjeta_kpi(
        "Forecast final",
        f"{forecast_last:.4f}" if forecast_last is not None else "N/D",
        help_text="Último valor pronosticado de volatilidad.",
        subtexto="Nivel esperado al final del horizonte forecast.",
    )

if modo == "Estadístico":
    extra1, extra2 = st.columns(2)

    with extra1:
        delta_text = ""
        if persistence is not None:
            if persistence >= 0.90:
                delta_text = "Alta persistencia"
            elif persistence >= 0.75:
                delta_text = "Persistencia media"
            else:
                delta_text = "Persistencia baja"

        tarjeta_kpi(
            "Persistencia",
            f"{persistence:.4f}" if persistence is not None else "N/D",
            delta_text,
            help_text="Memoria de los choques de volatilidad en la dinámica estimada.",
            subtexto="Qué tanto duran los choques en la varianza condicional.",
        )

    with extra2:
        tarjeta_kpi(
            "Volatilidad largo plazo",
            f"{long_run_vol:.4f}" if long_run_vol is not None else "N/D",
            help_text="Nivel al que tendería la volatilidad si el modelo es estacionario.",
            subtexto="Punto de convergencia del modelo bajo reversión a la media.",
        )

plot_card_footer(interpret_kpis(best_model, forecast_last, persistence, long_run_vol))

# ==============================
# INTERPRETACIÓN AUTOMÁTICA
# ==============================
seccion("Interpretación")

if results["best_model_name"] is not None and results.get("summary_text"):
    nota(results["summary_text"])
else:
    st.warning("No se generó un resumen automático del mejor modelo.")

# ==============================
# COMPARACIÓN DE MODELOS
# ==============================
seccion("Comparación De Modelos")

if mostrar_tablas:
    st.dataframe(results["comparison"], use_container_width=True)
else:
    with st.expander("Ver comparación completa de modelos"):
        st.dataframe(results["comparison"], use_container_width=True)

# ==============================
# GRÁFICOS
# ==============================
seccion("Volatilidad Y Pronóstico")

g1, g2 = st.columns(2, gap="large")

with g1:
    plot_card_header(
        "Volatilidad condicional estimada",
        "Muestra cómo cambia la volatilidad estimada del activo a lo largo del tiempo bajo los modelos ajustados.",
        modo=modo,
        caption="Activa o desactiva las series para comparar fácilmente ARCH, GARCH y EGARCH.",
    )

    toolbar_label("Capas del gráfico")
    vg1, vg2, vg3, vg4 = st.columns(4)
    with vg1:
        show_arch = st.checkbox("ARCH", value=True, key="garch_show_arch")
    with vg2:
        show_garch = st.checkbox("GARCH", value=True, key="garch_show_garch")
    with vg3:
        show_egarch = st.checkbox("EGARCH", value=True, key="garch_show_egarch")
    with vg4:
        smooth_view = st.checkbox("Vista limpia", value=False, key="garch_clean_vol")

    fig_vol = plot_volatility(results["volatility"])
    fig_vol = style_plot(fig_vol, modo)

    fig_vol.update_layout(
        title=dict(
            text="Volatilidad Condicional Estimada",
            x=0.03,
            xanchor="left",
            y=0.97,
            yanchor="top",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    for trace in fig_vol.data:
        trace_name = str(getattr(trace, "name", "") or "").lower()

        if "egarch" in trace_name:
            trace.visible = True if show_egarch else "legendonly"
            trace.line.color = "#F9A8D4"
            trace.line.width = 2.2

        elif "garch" in trace_name:
            trace.visible = True if show_garch else "legendonly"
            trace.line.color = "#22C55E"
            trace.line.width = 2.35

        elif "arch" in trace_name:
            trace.visible = True if show_arch else "legendonly"
            trace.line.color = "#93C5FD"
            trace.line.width = 2.0

    if smooth_view:
        try:
            fig_vol.update_layout(showlegend=False)
        except Exception:
            pass

    st.plotly_chart(fig_vol, use_container_width=True)
    plot_card_footer(interpret_volatility())

with g2:
    plot_card_header(
        "Forecast de volatilidad",
        "Resume la trayectoria esperada de la volatilidad futura bajo el mejor modelo seleccionado.",
        modo=modo,
        caption="Puedes activar o desactivar la referencia de largo plazo y limpiar la lectura del forecast.",
    )

    toolbar_label("Capas del gráfico")
    fg1, fg2, fg3 = st.columns(3)
    with fg1:
        show_forecast = st.checkbox("Pronóstico", value=True, key="garch_show_forecast")
    with fg2:
        show_long_run_local = st.checkbox(
            "Largo plazo",
            value=mostrar_long_run,
            key="garch_show_long_run_local"
        )
    with fg3:
        clean_forecast = st.checkbox("Vista limpia", value=False, key="garch_clean_forecast")

    fig_forecast = plot_forecast(
        results["forecast"],
        long_run_vol=long_run_vol if show_long_run_local else None,
    )
    fig_forecast = style_plot(fig_forecast, modo)

    fig_forecast.update_layout(
        title=dict(
            text="Pronóstico De Volatilidad",
            x=0.03,
            xanchor="left",
            y=0.97,
            yanchor="top",
        ),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    for trace in fig_forecast.data:
        trace_name = str(getattr(trace, "name", "") or "").lower()

        if any(k in trace_name for k in ["forecast", "pronostic", "volatilidad_pronosticada"]):
            trace.visible = True if show_forecast else "legendonly"
            try:
                trace.line.color = "#7DD3FC"
                trace.line.width = 2.5
            except Exception:
                pass

        elif any(k in trace_name for k in ["long", "largo", "run", "plazo"]):
            trace.visible = True if show_long_run_local else "legendonly"
            try:
                trace.line.color = "#FBBF24"
                trace.line.dash = "dot"
                trace.line.width = 2.0
            except Exception:
                pass

    if clean_forecast:
        try:
            fig_forecast.update_layout(showlegend=False)
        except Exception:
            pass

    st.plotly_chart(fig_forecast, use_container_width=True)
    plot_card_footer(interpret_forecast(show_long_run_local, long_run_vol))

# ==============================
# LECTURA DIDÁCTICA
# ==============================
if modo == "General":
    nota(
        "La volatilidad condicional permite ver cuándo el activo atraviesa fases de mayor o menor incertidumbre. "
        "El forecast agrega una lectura prospectiva del riesgo, y la referencia de largo plazo ayuda a entender la reversión a la media."
    )

# ==============================
# DIAGNÓSTICO
# ==============================
if modo == "Estadístico" and mostrar_diagnostico:
    seccion("Diagnóstico")

    plot_card_header(
        "Diagnóstico del modelo",
        "Permite revisar medidas complementarias del ajuste para validar la especificación elegida.",
        modo=modo,
        caption="Úsalo como soporte de sustentación técnica del modelo.",
    )
    st.dataframe(results["diagnostics"], use_container_width=True)

# ==============================
# RESIDUOS ESTANDARIZADOS
# ==============================
if modo == "Estadístico" and mostrar_residuos:
    seccion("Residuos Estandarizados")

    plot_card_header(
        "Residuos estandarizados",
        "Sirven para revisar si el modelo absorbió adecuadamente la dinámica de volatilidad.",
        modo=modo,
        caption="Muestra las observaciones más recientes para revisión rápida.",
    )
    st.dataframe(results["std_resid"].tail(20), use_container_width=True)