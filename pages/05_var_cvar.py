import streamlit as st
import numpy as np
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

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import load_market_bundle
from src.risk_metrics import risk_comparison_table, kupiec_test
from src.plots import plot_var_distribution

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
        margin=dict(l=20, r=20, t=70, b=20),
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


def interpret_risk_summary(alpha, var_h, cvar_h, var_p, var_mc):
    parts = []

    if var_h is not None:
        parts.append(f"Con {int(alpha * 100)}% de confianza, el VaR histórico diario es {var_h:.2%}")
    if cvar_h is not None:
        parts.append(f"y el CVaR histórico diario asciende a {cvar_h:.2%}")
    if var_p is not None:
        parts.append(f". El VaR paramétrico se estima en {var_p:.2%}")
    if var_mc is not None:
        parts.append(f"y el VaR Monte Carlo en {var_mc:.2%}")

    text = " ".join(parts).strip()
    if not text:
        return "No fue posible construir una interpretación automática del resumen de riesgo extremo."
    return text + "." if not text.endswith(".") else text


def interpret_distribution_chart():
    return "El histograma resume la distribución empírica de rendimientos del portafolio. Las líneas de VaR y CVaR permiten comparar umbrales de pérdida y severidad extrema bajo distintos métodos."


def interpret_kupiec(kupiec):
    if not kupiec:
        return "No fue posible ejecutar el test de Kupiec."

    return (
        f"Se observaron {kupiec['violations']} violaciones del VaR. "
        f"La tasa observada fue {kupiec['observed_fail_rate'] * 100:.2f}% frente a una tasa esperada de "
        f"{kupiec['expected_fail_rate'] * 100:.2f}%. "
        f"El p-valor del test es {kupiec['p_value']:.4f}."
    )


def get_portfolio_metadata():
    return [{"nombre": nombre, "ticker": meta["ticker"]} for nombre, meta in ASSETS.items()]


def build_sidebar_weights(portfolio_meta: list[dict]):
    st.markdown("### Pesos Del Portafolio")
    st.caption("Asigna pesos manualmente. Se normalizan automáticamente para que sumen 100%.")

    raw_weights = []
    for i, item in enumerate(portfolio_meta):
        raw_value = st.number_input(
            f"Peso {item['nombre']}",
            min_value=0.0,
            max_value=100.0,
            value=round(100 / len(portfolio_meta), 2),
            step=1.0,
            key=f"var_weight_{i}",
        )
        raw_weights.append(raw_value / 100.0)

    raw_weights = np.array(raw_weights, dtype=float)
    total = raw_weights.sum()

    if total <= 0:
        normalized = np.repeat(1 / len(portfolio_meta), len(portfolio_meta))
        st.warning("Los pesos ingresados suman 0. Se aplicó equiponderación por defecto.")
    else:
        normalized = raw_weights / total

    weights_df = pd.DataFrame(
        {
            "Activo": [item["nombre"] for item in portfolio_meta],
            "Ticker": [item["ticker"] for item in portfolio_meta],
            "Peso": normalized,
        }
    )

    st.caption(f"Suma normalizada de pesos: {normalized.sum():.2%}")
    return normalized, weights_df


# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros De Riesgo Extremo",
    filtros_expanded=False,
)

portfolio_meta = get_portfolio_metadata()

# ==============================
# SIDEBAR
# ==============================
with filtros_sidebar:
    horizonte = st.selectbox(
        "Horizonte histórico de análisis",
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
        key="var_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="var_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="var_end")

    alpha = st.select_slider(
        "Nivel de confianza",
        options=[0.95, 0.96, 0.97, 0.98, 0.99],
        value=0.95,
        key="varcvar_alpha",
    )

    mostrar_tablas = st.checkbox("Mostrar tablas completas", value=False, key="var_show_tables")
    mostrar_backtesting = st.checkbox("Mostrar backtesting", value=True, key="var_show_backtesting")

    mostrar_fundamento = False
    mostrar_interpretacion_tecnica = False

    if modo == "Estadístico":
        mostrar_fundamento = st.checkbox("Mostrar fundamento teórico", value=False, key="var_show_fundamento")
        mostrar_interpretacion_tecnica = st.checkbox(
            "Mostrar interpretación técnica",
            value=True,
            key="var_show_tecnica",
        )

        n_sim = st.slider(
            "Simulaciones Monte Carlo",
            min_value=5000,
            max_value=50000,
            value=10000,
            step=5000,
            key="var_n_sim",
        )
    else:
        n_sim = 10000

    st.markdown("---")
    weights, pesos_df = build_sidebar_weights(portfolio_meta)

# ==============================
# CARGA Y PREPARACIÓN DE DATOS
# ==============================
tickers = [item["ticker"] for item in portfolio_meta]
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))
returns = bundle["returns"].replace([np.inf, -np.inf], np.nan).dropna()

if returns.empty or len(returns) < 30:
    st.error("No hay suficientes datos para calcular métricas de riesgo.")
    st.stop()

available_tickers = [ticker for ticker in tickers if ticker in returns.columns]

if len(available_tickers) < 2:
    st.error("No hay suficientes activos disponibles en la matriz de rendimientos para construir el portafolio.")
    st.stop()

pesos_df_validos = pesos_df[pesos_df["Ticker"].isin(available_tickers)].copy()

if pesos_df_validos.empty:
    st.error("No fue posible alinear los pesos con los activos disponibles en los datos descargados.")
    st.stop()

weights_valid = pesos_df_validos["Peso"].to_numpy(dtype=float)
weights_valid = weights_valid / weights_valid.sum()

pesos_df_validos["Peso"] = weights_valid
returns = returns[available_tickers]
portfolio_returns = returns.mul(weights_valid, axis=1).sum(axis=1)

table = risk_comparison_table(
    portfolio_returns=portfolio_returns,
    asset_returns_df=returns,
    weights=weights_valid,
    alpha=alpha,
    n_sim=n_sim,
)

if table.empty:
    st.error("No fue posible calcular VaR y CVaR con los datos disponibles.")
    st.stop()

# ==============================
# FILAS POR MÉTODO
# ==============================
var_hist_row = table.loc[table["método"] == "Histórico"]
var_param_row = table.loc[table["método"] == "Paramétrico"]
var_mc_row = table.loc[table["método"] == "Monte Carlo"]

var_h = float(var_hist_row["VaR_diario"].iloc[0]) if not var_hist_row.empty else None
cvar_h = float(var_hist_row["CVaR_diario"].iloc[0]) if not var_hist_row.empty else None
var_p = float(var_param_row["VaR_diario"].iloc[0]) if not var_param_row.empty else None
cvar_p = float(var_param_row["CVaR_diario"].iloc[0]) if not var_param_row.empty else None
var_mc = float(var_mc_row["VaR_diario"].iloc[0]) if not var_mc_row.empty else None
cvar_mc = float(var_mc_row["CVaR_diario"].iloc[0]) if not var_mc_row.empty else None

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 5 - VaR y CVaR",
    "Evalúa el riesgo extremo del portafolio mediante VaR y CVaR bajo distintos enfoques de estimación",
    modo=modo,
)

if modo == "General":
    nota("Este módulo traduce el riesgo extremo del portafolio en pérdidas umbral y pérdidas medias severas bajo escenarios adversos.")
else:
    nota("En modo estadístico se comparan VaR y CVaR bajo enfoques paramétrico, histórico y Monte Carlo, junto con validación por backtesting.")

# ==============================
# TABS
# ==============================
tab1, tab2, tab3 = st.tabs([
    "Resumen y KPIs",
    "Distribución de riesgo",
    "Comparación y backtesting",
])

# ==============================
# TAB 1
# ==============================
with tab1:
    seccion("Resumen Del Módulo")

    if modo == "General":
        nota(
            f"Se estima cuánto podría perder el portafolio con un nivel de confianza del {int(alpha * 100)}%. "
            "El VaR representa una pérdida umbral y el CVaR resume la severidad promedio de la cola extrema."
        )
    else:
        nota(
            f"Se comparan VaR y CVaR del portafolio con pesos personalizados al nivel de confianza del {int(alpha * 100)}% "
            "bajo enfoques paramétrico, histórico y Monte Carlo."
        )

    if modo == "Estadístico" and mostrar_fundamento:
        seccion("Fundamento Teórico")

        st.markdown(
            r"""
            Sea \(R_{p,t}\) el rendimiento del portafolio en el periodo \(t\). En este análisis, la pérdida se define como:
            """
        )
        st.latex(r"L_t = -R_{p,t}")

        nota(
            "Con esta convención, pérdidas positivas implican escenarios adversos. El VaR corresponde al cuantil de la distribución de pérdidas y el CVaR mide la pérdida promedio cuando ya se superó ese umbral."
        )

        st.info(
            """
            - **Paramétrico:** supone normalidad de rendimientos.
            - **Histórico:** usa la distribución empírica observada.
            - **Monte Carlo:** simula escenarios a partir de la media y la covarianza de los activos.
            """
        )

    seccion("Portafolio Analizado")

    pesos_show = pesos_df_validos[["Activo", "Ticker", "Peso"]].copy()
    pesos_show["Peso"] = pesos_show["Peso"].map(lambda x: f"{x:.2%}")

    if modo == "General":
        nota("Los pesos del portafolio se ajustan desde el panel lateral y se normalizan automáticamente para que sumen 100%.")
        st.dataframe(pesos_show, use_container_width=True)
    else:
        st.dataframe(pesos_show, use_container_width=True)

    seccion("KPIs De Riesgo")

    var_delta = ""
    if var_h is not None and cvar_h is not None:
        gap_hist = cvar_h - var_h
        var_delta = f"Brecha cola: {gap_hist:.2%}"

    cvar_delta = "Más severo que VaR" if cvar_h is not None and var_h is not None else ""

    param_delta = ""
    if var_p is not None and var_h is not None:
        if var_p > var_h:
            param_delta = "Más conservador"
        elif var_p < var_h:
            param_delta = "Menos conservador"
        else:
            param_delta = "Muy similar al histórico"

    mc_delta = ""
    if var_mc is not None and var_h is not None:
        if var_mc > var_h:
            mc_delta = "Simulación más severa"
        elif var_mc < var_h:
            mc_delta = "Simulación menos severa"
        else:
            mc_delta = "Muy similar al histórico"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tarjeta_kpi(
            f"VaR histórico {int(alpha * 100)}%",
            f"{var_h:.2%}" if var_h is not None else "N/D",
            var_delta,
            help_text="Pérdida umbral estimada con enfoque histórico.",
            subtexto="Umbral de pérdida diaria bajo la distribución observada.",
        )

    with col2:
        tarjeta_kpi(
            f"CVaR histórico {int(alpha * 100)}%",
            f"{cvar_h:.2%}" if cvar_h is not None else "N/D",
            cvar_delta,
            help_text="Pérdida promedio condicionada a superar el VaR.",
            subtexto="Severidad media una vez se supera el VaR.",
        )

    with col3:
        tarjeta_kpi(
            "VaR paramétrico",
            f"{var_p:.2%}" if var_p is not None else "N/D",
            param_delta,
            help_text="Estimado bajo supuesto de normalidad.",
            subtexto="Cálculo cerrado bajo media y desviación estándar.",
        )

    with col4:
        tarjeta_kpi(
            "VaR Monte Carlo",
            f"{var_mc:.2%}" if var_mc is not None else "N/D",
            mc_delta,
            help_text="Estimado mediante simulación probabilística.",
            subtexto="Riesgo extremo aproximado a partir de simulación.",
        )

    plot_card_footer(interpret_risk_summary(alpha, var_h, cvar_h, var_p, var_mc))

# ==============================
# TAB 2
# ==============================
with tab2:
    seccion("Distribución Y Riesgo Extremo")

    plot_card_header(
        "Distribución de rendimientos del portafolio",
        "El histograma muestra la forma empírica de los rendimientos y las líneas señalan los umbrales de VaR y CVaR por método.",
        modo=modo,
        caption="Puedes activar o desactivar líneas de riesgo para simplificar la lectura.",
    )

    toolbar_label("Capas del gráfico")
    vg1, vg2, vg3, vg4 = st.columns(4)
    with vg1:
        show_hist = st.checkbox("Histograma", value=True, key="var_show_hist")
    with vg2:
        show_var = st.checkbox("Líneas VaR", value=True, key="var_show_var")
    with vg3:
        show_cvar = st.checkbox("Líneas CVaR", value=True, key="var_show_cvar")
    with vg4:
        clean_view = st.checkbox("Vista limpia", value=False, key="var_clean_view")

    fig = plot_var_distribution(portfolio_returns, table)
    fig = style_plot(fig, modo)

    fig.update_layout(
        title=dict(
            text="Distribución De Rendimientos Y Riesgo Extremo",
            x=0.03,
            xanchor="left",
            y=0.97,
            yanchor="top",
        ),
        margin=dict(l=20, r=20, t=70, b=20),
    )

    for trace in fig.data:
        trace_name = str(getattr(trace, "name", "") or "").lower()

        if any(k in trace_name for k in ["hist", "histograma", "returns", "rendimientos"]):
            trace.visible = True if show_hist else "legendonly"
            try:
                trace.marker.color = "#7DD3FC" if modo == "General" else "#F9A8D4"
            except Exception:
                pass

        elif "cvar" in trace_name:
            trace.visible = True if show_cvar else "legendonly"
            try:
                trace.line.color = "#FB7185" if modo == "Estadístico" else "#EF4444"
                trace.line.dash = "dot"
                trace.line.width = 2.4
            except Exception:
                pass

        elif "var" in trace_name:
            trace.visible = True if show_var else "legendonly"
            try:
                trace.line.color = "#FBBF24"
                trace.line.dash = "dash"
                trace.line.width = 2.2
            except Exception:
                pass

    if clean_view:
        try:
            fig.update_layout(showlegend=False)
        except Exception:
            pass

    st.plotly_chart(fig, use_container_width=True)
    plot_card_footer(interpret_distribution_chart())

# ==============================
# TAB 3
# ==============================
with tab3:
    seccion("Comparación VaR / CVaR")

    if mostrar_tablas:
        st.dataframe(table, use_container_width=True)
    else:
        with st.expander("Ver tabla completa de VaR y CVaR"):
            st.dataframe(table, use_container_width=True)

    seccion("Interpretación")

    lectura_simple = f"""
    Con {int(alpha * 100)}% de confianza, la pérdida diaria del portafolio no superaría aproximadamente **{var_h:.2%}**.
    Si el evento extremo supera ese umbral, la pérdida promedio podría acercarse a **{cvar_h:.2%}**.
    """
    st.success(lectura_simple)

    if modo == "Estadístico" and mostrar_interpretacion_tecnica:
        interpretacion_tecnica = []

        if var_h is not None and cvar_h is not None:
            interpretacion_tecnica.append(
                f"El VaR histórico diario del portafolio es {var_h:.2%} y el CVaR histórico diario es {cvar_h:.2%}."
            )
            interpretacion_tecnica.append(
                "El CVaR supera al VaR porque mide la severidad promedio dentro de la cola extrema."
            )

        if var_p is not None and var_h is not None:
            if var_p < var_h:
                interpretacion_tecnica.append(
                    "El VaR paramétrico es menor que el histórico, lo que puede sugerir subestimación del riesgo bajo normalidad."
                )
            elif var_p > var_h:
                interpretacion_tecnica.append(
                    "El VaR paramétrico es mayor que el histórico, señal de una estimación más conservadora."
                )
            else:
                interpretacion_tecnica.append(
                    "El VaR paramétrico y el histórico son muy similares para esta muestra."
                )

        if var_mc is not None:
            interpretacion_tecnica.append(
                f"El VaR Monte Carlo diario estimado es {var_mc:.2%}, útil para contrastar sensibilidad ante simulación."
            )

        for msg in interpretacion_tecnica:
            nota(msg)

    with st.expander("Ver interpretación técnica completa"):
        st.write(
            """
            El VaR resume una pérdida umbral bajo un nivel de confianza dado, mientras que el CVaR
            captura la pérdida promedio cuando ese umbral ya fue superado. Por eso el CVaR ofrece
            una lectura más sensible del riesgo extremo y de la cola de pérdidas.
            """
        )

    if mostrar_backtesting:
        seccion("Backtesting VaR - Test De Kupiec")

        if var_h is not None:
            kupiec = kupiec_test(
                returns=portfolio_returns,
                var=var_h,
                alpha=alpha,
            )

            if kupiec:
                k1, k2, k3 = st.columns(3)

                with k1:
                    tarjeta_kpi(
                        "Violaciones",
                        str(kupiec["violations"]),
                        help_text="Número de veces que la pérdida superó el VaR histórico.",
                        subtexto="Excesos observados frente al umbral estimado.",
                    )

                with k2:
                    tarjeta_kpi(
                        "Observadas (%)",
                        f"{kupiec['observed_fail_rate'] * 100:.2f}%",
                        help_text="Frecuencia empírica de violaciones del VaR.",
                        subtexto="Tasa real registrada en la muestra.",
                    )

                with k3:
                    tarjeta_kpi(
                        "Esperadas (%)",
                        f"{kupiec['expected_fail_rate'] * 100:.2f}%",
                        help_text="Frecuencia teórica esperada bajo el nivel de confianza elegido.",
                        subtexto="Tasa teórica coherente con el nivel de confianza.",
                    )

                plot_card_footer(interpret_kupiec(kupiec))

                st.write(f"**p-value:** {kupiec['p_value']:.4f}")
                st.write(f"**Conclusión:** {kupiec['conclusion']}")

                if kupiec["p_value"] > 0.05:
                    st.success(
                        "El VaR histórico es consistente con la frecuencia de pérdidas observadas en la muestra."
                    )
                else:
                    st.error(
                        "El VaR histórico no es consistente con la frecuencia de pérdidas observadas. Esto sugiere una posible mala calibración del modelo."
                    )

                if modo == "Estadístico":
                    with st.expander("Ver explicación del test de Kupiec"):
                        st.info(
                            "El test de Kupiec compara la proporción esperada de violaciones del VaR con la proporción observada para evaluar si el modelo de riesgo está razonablemente calibrado."
                        )
                else:
                    nota("Este bloque verifica si el VaR estimado fue razonable frente a las pérdidas observadas.")
            else:
                st.warning("No se pudo ejecutar el test de Kupiec.")
        else:
            st.warning("No hay VaR histórico disponible para ejecutar el test de Kupiec.")