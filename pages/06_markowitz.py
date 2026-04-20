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
from src.markowitz import (
    simulate_portfolios,
    efficient_frontier,
    minimum_variance_portfolio,
    maximum_sharpe_portfolio,
    weights_table,
)
from src.plots import plot_correlation_heatmap, plot_frontier
from src.api.macro import macro_snapshot
from src.portfolio_optimization import optimize_target_return

ensure_project_dirs()


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

    try:
        fig.update_coloraxes(
            colorbar=dict(
                tickfont=dict(color=tick_color, size=11),
                title=dict(font=dict(color=axis_title, size=12)),
            )
        )
    except Exception:
        pass

    return fig


def ensure_dataframe(obj):
    if isinstance(obj, pd.Series):
        return obj.to_frame().T
    if isinstance(obj, pd.DataFrame):
        return obj
    return pd.DataFrame([obj])


def safe_get_first(obj, key):
    try:
        if isinstance(obj, pd.Series):
            return obj.get(key, None)
        if isinstance(obj, pd.DataFrame):
            if key in obj.columns and not obj.empty:
                return obj[key].iloc[0]
        if isinstance(obj, dict):
            return obj.get(key, None)
    except Exception:
        return None
    return None


def format_weights_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    cols = {c.lower(): c for c in out.columns}

    activo_col = cols.get("activo", list(out.columns)[0])
    peso_col = cols.get("peso", list(out.columns)[1])

    out = out[[activo_col, peso_col]].copy()
    out.columns = ["Activo", "Peso"]
    out["Peso"] = pd.to_numeric(out["Peso"], errors="coerce")
    out["Participación"] = out["Peso"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "N/D")
    out["Peso"] = out["Peso"].round(4)
    out = out.sort_values("Peso", ascending=False).reset_index(drop=True)
    return out


def interpret_kpis(n_assets, n_obs, n_portfolios, rf_annual):
    return (
        f"Se analizaron {n_assets} activos con {n_obs} observaciones alineadas y se simularon "
        f"{n_portfolios:,} portafolios usando una tasa libre de riesgo de {rf_annual:.2%}."
    ).replace(",", ".")


def interpret_optimal_portfolios(min_var_return, min_var_vol, max_sharpe_return, max_sharpe_ratio):
    parts = []

    if min_var_return is not None and min_var_vol is not None:
        parts.append(
            f"El portafolio de mínima varianza ofrece un retorno esperado de {float(min_var_return):.2%} "
            f"con volatilidad de {float(min_var_vol):.2%}"
        )

    if max_sharpe_return is not None and max_sharpe_ratio is not None:
        parts.append(
            f"mientras que el portafolio de máximo Sharpe alcanza un retorno esperado de {float(max_sharpe_return):.2%} "
            f"con ratio Sharpe de {float(max_sharpe_ratio):.3f}"
        )

    text = ". ".join(parts).strip()
    if not text:
        return "No fue posible construir una interpretación automática de los portafolios óptimos."
    return text + "." if not text.endswith(".") else text


def interpret_correlation():
    return "La matriz de correlación ayuda a identificar qué tan parecidos son los movimientos entre activos. Correlaciones más bajas suelen mejorar el potencial de diversificación del portafolio."


def interpret_frontier():
    return "La frontera eficiente resume las mejores combinaciones riesgo-retorno encontradas. Los portafolios destacados permiten comparar estabilidad, eficiencia y metas de rentabilidad."


def build_target_weights_df(returns: pd.DataFrame, weights: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "Activo": returns.columns,
            "Peso": np.round(weights, 4),
        }
    )
    out["Participación"] = out["Peso"].map(lambda x: f"{x:.2%}")
    return out.sort_values("Peso", ascending=False).reset_index(drop=True)


# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros De Optimización",
    filtros_expanded=False,
)

# ==============================
# SIDEBAR
# ==============================
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
        key="mk_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="mk_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="mk_end")

    mostrar_tablas = st.checkbox("Mostrar tablas completas", value=False, key="mk_show_tables")

    with st.expander("Filtros secundarios", expanded=False):
        n_portfolios = st.slider(
            "Número de portafolios",
            min_value=5000,
            max_value=50000,
            value=10000,
            step=5000,
            key="mk_n_portfolios",
        )

        target_return_pct = st.number_input(
            "Retorno anual objetivo del portafolio (%)",
            min_value=0.0,
            max_value=30.0,
            value=10.0,
            step=0.5,
            key="mk_target_return_pct",
            help="Ingresa el retorno objetivo en porcentaje. Ejemplo: 10 equivale a 10%.",
        )
        target_return = target_return_pct / 100

        if modo == "Estadístico":
            mostrar_detalle_correlacion = st.checkbox(
                "Mostrar matriz de correlación tabular",
                value=False,
                key="mk_show_corr_table",
            )
            mostrar_interpretacion_tecnica = st.checkbox(
                "Mostrar interpretación técnica",
                value=True,
                key="mk_show_tech_interp",
            )
        else:
            mostrar_detalle_correlacion = False
            mostrar_interpretacion_tecnica = False

# ==============================
# CARGA DE DATOS
# ==============================
tickers = [meta["ticker"] for meta in ASSETS.values()]
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))

returns = (
    bundle["returns"]
    .replace([np.inf, -np.inf], np.nan)
    .dropna(how="any")
)

if returns.empty or returns.shape[0] < 2 or returns.shape[1] < 2:
    st.error("No hay suficientes datos de retornos alineados para ejecutar Markowitz.")
    st.write({
        "shape_returns": bundle["returns"].shape,
        "na_por_activo": bundle["returns"].isna().sum().to_dict(),
    })
    st.stop()

macro = macro_snapshot()
rf_annual = (
    macro["risk_free_rate_pct"] / 100
    if macro["risk_free_rate_pct"] == macro["risk_free_rate_pct"]
    else 0.03
)

# ==============================
# SIMULACIÓN Y SOLUCIONES ÓPTIMAS
# ==============================
sim_df = simulate_portfolios(returns, rf_annual=rf_annual, n_portfolios=n_portfolios)

if sim_df.empty:
    st.error("La simulación de portafolios no generó resultados válidos.")
    st.write({
        "shape_returns_filtrado": returns.shape,
        "rf_annual": rf_annual,
        "n_portfolios": n_portfolios,
    })
    st.stop()

frontier_df = efficient_frontier(sim_df)
min_var = minimum_variance_portfolio(sim_df)
max_sharpe = maximum_sharpe_portfolio(sim_df)

if min_var is None or max_sharpe is None:
    st.error("No fue posible identificar los portafolios óptimos.")
    st.stop()

min_var_df = ensure_dataframe(min_var)
max_sharpe_df = ensure_dataframe(max_sharpe)

if min_var_df.empty or max_sharpe_df.empty:
    st.error("No fue posible identificar los portafolios óptimos.")
    st.stop()

min_var_weights_df = format_weights_df(weights_table(min_var))
max_sharpe_weights_df = format_weights_df(weights_table(max_sharpe))
corr = returns.corr()

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 6 - Optimización de portafolio (Markowitz)",
    "Explora portafolios eficientes, diversificación, relación riesgo-retorno y soluciones óptimas bajo Markowitz",
    modo=modo,
)

if modo == "General":
    nota("Este módulo compara combinaciones de portafolios para mostrar cómo cambia el equilibrio entre retorno esperado y riesgo.")
else:
    nota("En modo estadístico se enfatiza el enfoque media-varianza, la frontera eficiente, el Sharpe y la sensibilidad de la solución a un retorno objetivo.")

# ==============================
# RESUMEN
# ==============================
seccion("Resumen Del Módulo")

if modo == "General":
    nota(
        "Este módulo construye múltiples combinaciones de portafolios para identificar aquellas que ofrecen una mejor relación entre retorno esperado y riesgo. Se resaltan el portafolio de mínima varianza, el de máximo Sharpe y una solución con retorno objetivo."
    )
else:
    nota(
        "Este módulo implementa el enfoque media-varianza de Markowitz, simulando portafolios factibles para aproximar la frontera eficiente, identificar el portafolio de mínima varianza, el de máximo Sharpe y resolver una optimización condicionada a un retorno objetivo."
    )

# ==============================
# TABS
# ==============================
tab1, tab2, tab3 = st.tabs([
    "Portafolios destacados",
    "Gráficas",
    "Composición óptima",
])

# ==============================
# KPIS PRINCIPALES
# ==============================
seccion("KPIs Del Módulo")

n_assets = returns.shape[1]
n_obs = returns.shape[0]

min_var_return = safe_get_first(min_var, "return")
min_var_vol = safe_get_first(min_var, "volatility")
max_sharpe_return = safe_get_first(max_sharpe, "return")
max_sharpe_vol = safe_get_first(max_sharpe, "volatility")
max_sharpe_ratio = safe_get_first(max_sharpe, "sharpe")

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Activos analizados",
        str(n_assets),
        help_text="Número de activos incluidos en el universo de optimización.",
        subtexto="Universo usado para construir combinaciones factibles.",
    )

with c2:
    tarjeta_kpi(
        "Observaciones",
        str(n_obs),
        help_text="Cantidad de rendimientos alineados usados en la estimación.",
        subtexto="Muestra histórica disponible para covarianzas y retornos.",
    )

with c3:
    tarjeta_kpi(
        "Portafolios simulados",
        f"{n_portfolios:,}".replace(",", "."),
        help_text="Combinaciones generadas para aproximar la frontera eficiente.",
        subtexto="Exploración aleatoria del espacio riesgo-retorno.",
    )

with c4:
    tarjeta_kpi(
        "Tasa libre de riesgo",
        f"{rf_annual:.2%}",
        help_text="Usada para calcular el ratio Sharpe.",
        subtexto="Referencia para medir eficiencia ajustada por riesgo.",
    )

plot_card_footer(interpret_kpis(n_assets, n_obs, n_portfolios, rf_annual))

# ==============================
# TAB 1
# ==============================
with tab1:
    seccion("Portafolios Destacados")

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        tarjeta_kpi(
            "Retorno mín. varianza",
            f"{float(min_var_return):.2%}" if min_var_return is not None else "N/D",
            help_text="Retorno esperado del portafolio más estable.",
            subtexto="Rentabilidad asociada a la cartera de menor volatilidad.",
        )

    with c6:
        tarjeta_kpi(
            "Volatilidad mín. varianza",
            f"{float(min_var_vol):.2%}" if min_var_vol is not None else "N/D",
            "Menor riesgo disponible",
            help_text="Portafolio con menor volatilidad estimada.",
            subtexto="Nivel mínimo de riesgo dentro del conjunto simulado.",
        )

    with c7:
        tarjeta_kpi(
            "Retorno máx. Sharpe",
            f"{float(max_sharpe_return):.2%}" if max_sharpe_return is not None else "N/D",
            help_text="Retorno esperado del portafolio más eficiente.",
            subtexto="Rentabilidad esperada del mejor balance riesgo-retorno.",
        )

    with c8:
        tarjeta_kpi(
            "Sharpe máximo",
            f"{float(max_sharpe_ratio):.3f}" if max_sharpe_ratio is not None else "N/D",
            "Mejor eficiencia riesgo-retorno",
            help_text="Portafolio con mayor ratio Sharpe.",
            subtexto="Exceso de retorno por unidad de volatilidad.",
        )

    plot_card_footer(
        interpret_optimal_portfolios(
            min_var_return, min_var_vol, max_sharpe_return, max_sharpe_ratio
        )
    )

# ==============================
# TAB 2
# ==============================
with tab2:
    seccion("Visualizaciones De Optimización")

    col_g1, col_g2 = st.columns(2, gap="large")

    with col_g1:
        plot_card_header(
            "Matriz de correlación",
            "La matriz de correlación ayuda a entender el potencial de diversificación entre los activos del portafolio.",
            modo=modo,
            caption="Activa o desactiva detalles para simplificar la lectura visual de la matriz.",
        )

        toolbar_label("Opciones de visualización")
        cg1, cg2 = st.columns(2)
        with cg1:
            clean_corr = st.checkbox("Vista limpia", value=False, key="mk_clean_corr")
        with cg2:
            show_corr_table_local = st.checkbox(
                "Ver tabla de correlación",
                value=mostrar_detalle_correlacion,
                key="mk_corr_table_local",
            )

        fig_corr = plot_correlation_heatmap(corr)
        fig_corr = style_plot(fig_corr, modo)
        fig_corr.update_layout(
            title=dict(
                text="Matriz De Correlación",
                x=0.03,
                xanchor="left",
                y=0.97,
                yanchor="top",
                font=dict(size=16, color="#0F172A"),
            ),
            margin=dict(l=20, r=20, t=70, b=20),
        )
        fig_corr.update_xaxes(tickfont=dict(size=11, color="#334155"))
        fig_corr.update_yaxes(tickfont=dict(size=11, color="#334155"))

        if clean_corr:
            try:
                fig_corr.update_layout(coloraxis_showscale=False)
            except Exception:
                pass

        st.plotly_chart(fig_corr, use_container_width=True)
        plot_card_footer(interpret_correlation())

        if show_corr_table_local:
            st.dataframe(corr.round(4), use_container_width=True)

    with col_g2:
        plot_card_header(
            "Frontera eficiente",
            "El gráfico resume el espacio de portafolios posibles y destaca la frontera eficiente junto con las soluciones óptimas.",
            modo=modo,
            caption="Mejoré leyenda, ejes y contraste para una lectura más clara.",
        )

        toolbar_label("Capas del gráfico")
        fg1, fg2, fg3, fg4 = st.columns(4)
        with fg1:
            show_cloud = st.checkbox("Nube", value=True, key="mk_show_cloud")
        with fg2:
            show_frontier = st.checkbox("Frontera", value=True, key="mk_show_frontier")
        with fg3:
            show_optima = st.checkbox("Óptimos", value=True, key="mk_show_optima")
        with fg4:
            clean_frontier = st.checkbox("Vista limpia", value=False, key="mk_clean_frontier")

        fig_frontier = plot_frontier(sim_df, frontier_df, min_var, max_sharpe)
        fig_frontier = style_plot(fig_frontier, modo)
        fig_frontier.update_layout(
            title=dict(
                text="Frontera Eficiente",
                x=0.03,
                xanchor="left",
                y=0.97,
                yanchor="top",
                font=dict(size=16, color="#0F172A"),
            ),
            margin=dict(l=20, r=20, t=70, b=20),
        )
        fig_frontier.update_xaxes(
            title_font=dict(size=14, color="#0F172A"),
            tickfont=dict(size=12, color="#334155"),
        )
        fig_frontier.update_yaxes(
            title_font=dict(size=14, color="#0F172A"),
            tickfont=dict(size=12, color="#334155"),
        )

        for trace in fig_frontier.data:
            trace_name = str(getattr(trace, "name", "") or "").lower()

            if any(k in trace_name for k in ["sim", "cloud", "nube", "portfolio", "portafolio"]):
                trace.visible = True if show_cloud else "legendonly"
                try:
                    if hasattr(trace, "marker"):
                        trace.marker.color = "#7DD3FC" if modo == "General" else "#F9A8D4"
                        trace.marker.opacity = 0.38
                        trace.marker.size = 6
                    if hasattr(trace, "line"):
                        trace.line.color = "#7DD3FC" if modo == "General" else "#F9A8D4"
                except Exception:
                    pass

            elif any(k in trace_name for k in ["frontier", "frontera", "efficient"]):
                trace.visible = True if show_frontier else "legendonly"
                try:
                    trace.line.color = "#D97706" if modo == "General" else "#BE123C"
                    trace.line.width = 4.8
                    trace.line.dash = "solid"
                except Exception:
                    pass

            elif any(k in trace_name for k in ["min", "sharpe", "ópt", "opt"]):
                trace.visible = True if show_optima else "legendonly"
                try:
                    if hasattr(trace, "marker"):
                        trace.marker.size = 11
                    if "min" in trace_name:
                        trace.marker.color = "#F97316"
                    elif "sharpe" in trace_name:
                        trace.marker.color = "#2563EB" if modo == "General" else "#7C3AED"
                except Exception:
                    pass

        try:
            fig_frontier.update_layout(
                legend=dict(
                    font=dict(size=11, color="#334155"),
                    bgcolor="rgba(255,255,255,0.92)",
                    bordercolor="rgba(148, 163, 184, 0.22)",
                    borderwidth=1,
                )
            )
        except Exception:
            pass

        if clean_frontier:
            try:
                fig_frontier.update_layout(showlegend=False)
            except Exception:
                pass

        st.plotly_chart(fig_frontier, use_container_width=True)
        plot_card_footer(interpret_frontier())

# ==============================
# TAB 3
# ==============================
with tab3:
    seccion("Composición De Portafolios Óptimos")

    col1, col2 = st.columns(2)

    with col1:
        plot_card_header(
            "Portafolio de mínima varianza",
            "Muestra la distribución de pesos del portafolio con menor volatilidad estimada.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(
            min_var_weights_df,
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        plot_card_header(
            "Portafolio de máximo Sharpe",
            "Muestra la distribución de pesos del portafolio con mejor eficiencia riesgo-retorno.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(
            max_sharpe_weights_df,
            use_container_width=True,
            hide_index=True,
        )

    if mostrar_tablas:
        with st.expander("Ver tablas completas de pesos y resultados"):
            st.markdown("#### Portafolio de mínima varianza")
            st.dataframe(min_var_df, use_container_width=True, hide_index=True)
            st.markdown("#### Portafolio de máximo Sharpe")
            st.dataframe(max_sharpe_df, use_container_width=True, hide_index=True)

    seccion("Optimización Con Retorno Objetivo")

    plot_card_header(
        "Solución condicionada",
        "Aquí se busca un portafolio que cumpla un retorno objetivo específico sujeto a las restricciones del modelo.",
        modo=modo,
        caption=f"Retorno objetivo configurado actualmente: {target_return:.2%}",
    )

    if target_return == 0:
        nota(
            "Un retorno objetivo de 0% no implica pesos iguales a cero. Bajo la formulación actual, el modelo sigue buscando una cartera completamente invertida cuya rentabilidad esperada sea cercana a 0%. Para representar 'no invertir' sería necesario incluir explícitamente cash o capital no asignado."
        )

    result = optimize_target_return(returns, target_return)

    if result is not None:
        target_delta = "Objetivo alcanzado" if result["return"] >= target_return else "Cercano al objetivo"

        col3, col4 = st.columns([1, 1.2])

        with col3:
            tarjeta_kpi(
                "Retorno esperado",
                f"{result['return']:.2%}",
                target_delta,
                help_text=f"Objetivo solicitado: {target_return:.2%}",
                subtexto="Rentabilidad estimada de la solución condicionada.",
            )

            tarjeta_kpi(
                "Volatilidad",
                f"{result['volatility']:.2%}",
                help_text="Riesgo estimado de la solución encontrada.",
                subtexto="Riesgo asociado al retorno objetivo impuesto.",
            )

        with col4:
            target_weights_df = build_target_weights_df(returns, result["weights"])
            st.dataframe(
                target_weights_df,
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("No se pudo encontrar solución para ese nivel de retorno.")

# ==============================
# INTERPRETACIÓN
# ==============================
seccion("Interpretación")

if modo == "General":
    nota(
        "Este módulo muestra que no existe una única mejor cartera: todo depende del equilibrio entre retorno y riesgo. La frontera eficiente resume las combinaciones más convenientes, mientras que mínima varianza, máximo Sharpe y retorno objetivo representan decisiones distintas dentro del mismo problema."
    )
else:
    if mostrar_interpretacion_tecnica:
        nota(
            "El enfoque de Markowitz modela la asignación óptima en términos de media y varianza. La frontera eficiente representa portafolios no dominados, el portafolio de mínima varianza minimiza el riesgo total, el de máximo Sharpe maximiza el exceso de retorno por unidad de riesgo y la solución con retorno objetivo impone una restricción adicional que puede exigir mayor volatilidad para alcanzar la meta."
        )