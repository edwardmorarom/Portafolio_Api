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
    GLOBAL_BENCHMARK,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    ensure_project_dirs,
)
from src.download import load_market_bundle
from src.preprocess import equal_weight_portfolio
from src.api.macro import macro_snapshot
from src.benchmark import benchmark_summary
from src.plots import plot_benchmark_base100

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
    return fig


def safe_metric(df: pd.DataFrame, filter_col: str, filter_val: str, value_col: str):
    try:
        return float(df.loc[df[filter_col] == filter_val, value_col].iloc[0])
    except Exception:
        return None


def delta_label(value, positive_text, negative_text, neutral_text="Sin cambio"):
    if value is None:
        return None
    if value > 0:
        return positive_text
    if value < 0:
        return negative_text
    return neutral_text


def interpret_macro_context(rf_pct, inflation_yoy, usdcop_market, cop_per_usd):
    parts = []

    if rf_pct is not None:
        parts.append(f"la tasa libre de riesgo se ubica en {rf_pct:.2f}%")

    if inflation_yoy is not None:
        parts.append(f"la inflación interanual se estima en {inflation_yoy:.2%}")

    if usdcop_market is not None and cop_per_usd is not None:
        if usdcop_market > cop_per_usd:
            parts.append("el USD/COP spot se encuentra por encima de su promedio anual")
        elif usdcop_market < cop_per_usd:
            parts.append("el USD/COP spot se encuentra por debajo de su promedio anual")
        else:
            parts.append("el USD/COP spot es similar a su promedio anual")

    if not parts:
        return "No fue posible construir una lectura automática del contexto macro."
    return "En el periodo analizado, " + ", ".join(parts) + "."


def interpret_relative_performance(ret_port, ret_bench, alpha_jensen, tracking_error):
    parts = []

    if ret_port is not None and ret_bench is not None:
        diff_ret = ret_port - ret_bench
        if diff_ret > 0:
            parts.append(f"el portafolio superó al benchmark por {diff_ret:.2%}")
        elif diff_ret < 0:
            parts.append(f"el portafolio quedó por debajo del benchmark en {abs(diff_ret):.2%}")
        else:
            parts.append("el portafolio tuvo un desempeño acumulado similar al benchmark")

    if alpha_jensen is not None:
        if alpha_jensen > 0:
            parts.append("el alpha de Jensen fue positivo")
        elif alpha_jensen < 0:
            parts.append("el alpha de Jensen fue negativo")
        else:
            parts.append("el alpha de Jensen fue cercano a cero")

    if tracking_error is not None:
        parts.append(f"el tracking error fue de {tracking_error:.4f}")

    if not parts:
        return "No fue posible construir una interpretación automática del desempeño relativo."
    return "En síntesis, " + ", ".join(parts) + "."


# ==============================
# ESTILOS LOCALES
# ==============================
st.markdown(
    """
    <style>
    .bm-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.7rem;
        margin-top: 0.4rem;
        margin-bottom: 1.1rem;
    }

    .bm-mini-meta {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 0.85rem;
        border-radius: 999px;
        background: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.30);
        font-size: 0.83rem;
        font-weight: 700;
        color: #334155 !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    .bm-mini-meta strong,
    .bm-mini-meta span,
    .bm-mini-meta div {
        color: #334155 !important;
    }

    .bm-mini-meta.benchmark-pill {
        background: #EEF2FF;
        border: 1px solid rgba(99, 102, 241, 0.30);
        color: #3730A3 !important;
    }

    .bm-mini-meta.benchmark-pill strong,
    .bm-mini-meta.benchmark-pill span,
    .bm-mini-meta.benchmark-pill div {
        color: #3730A3 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# SETUP GLOBAL
# ==============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros De Benchmark",
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
        key="bm_horizonte",
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
            start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="bm_start")
        with c2:
            end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="bm_end")

    mostrar_tablas = st.checkbox("Mostrar tablas completas", value=False, key="bm_show_tables")

    with st.expander("Filtros secundarios", expanded=False):
        if modo == "Estadístico":
            mostrar_interpretacion_tecnica = st.checkbox(
                "Mostrar interpretación técnica",
                value=True,
                key="bm_show_tech_interp",
            )
            mostrar_estado_macro = st.checkbox(
                "Mostrar estado de carga macro",
                value=False,
                key="bm_show_macro_status",
            )
        else:
            mostrar_interpretacion_tecnica = False
            mostrar_estado_macro = st.checkbox(
                "Mostrar estado de carga macro",
                value=False,
                key="bm_show_macro_status_general",
            )

# ==============================
# DATOS
# ==============================
tickers = [meta["ticker"] for meta in ASSETS.values()] + [GLOBAL_BENCHMARK]
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))
returns = bundle["returns"].dropna()

if returns.empty or GLOBAL_BENCHMARK not in returns.columns:
    st.error("No fue posible construir benchmark global.")
    st.stop()

portfolio_returns = equal_weight_portfolio(
    returns[[c for c in returns.columns if c != GLOBAL_BENCHMARK]]
)
benchmark_returns = returns[GLOBAL_BENCHMARK]

macro = macro_snapshot()
rf_annual = (
    macro["risk_free_rate_pct"] / 100
    if macro["risk_free_rate_pct"] == macro["risk_free_rate_pct"]
    else 0.03
)

summary_df, extras_df, cum_port, cum_bench = benchmark_summary(
    portfolio_returns=portfolio_returns,
    benchmark_returns=benchmark_returns,
    rf_annual=rf_annual,
)

rf_pct = macro["risk_free_rate_pct"] if macro["risk_free_rate_pct"] == macro["risk_free_rate_pct"] else None
inflation_yoy = macro["inflation_yoy"] if macro["inflation_yoy"] == macro["inflation_yoy"] else None
usdcop_market = macro["usdcop_market"] if macro["usdcop_market"] == macro["usdcop_market"] else None
cop_per_usd = macro["cop_per_usd"] if macro["cop_per_usd"] == macro["cop_per_usd"] else None

ret_port = safe_metric(summary_df, "serie", "Portafolio", "ret_acumulado")
ret_bench = safe_metric(summary_df, "serie", "Benchmark", "ret_acumulado")
alpha_jensen = safe_metric(extras_df, "métrica", "Alpha de Jensen", "valor")
tracking_error = safe_metric(extras_df, "métrica", "Tracking Error", "valor")
information_ratio = safe_metric(extras_df, "métrica", "Information Ratio", "valor")
max_drawdown = safe_metric(extras_df, "métrica", "Máximo drawdown", "valor")

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 8 - Contexto macro y benchmark",
    "Compara el desempeño del portafolio frente a un benchmark global y contextualiza los resultados con variables macroeconómicas",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo permite comparar si el portafolio tuvo un comportamiento mejor, similar o peor que su benchmark, y además ubica ese resultado dentro del entorno macroeconómico observado."
    )
else:
    nota(
        "En modo estadístico se enfatiza el análisis de desempeño relativo frente al benchmark mediante métricas como Alpha de Jensen, Tracking Error, Information Ratio y drawdown, complementadas con contexto macroeconómico."
    )

if "source" in macro and macro["source"]:
    st.caption(f"Fuente macro: {macro['source']}")
if "last_updated" in macro and macro["last_updated"]:
    st.caption(f"Última actualización macro: {macro['last_updated']}")

# ==============================
# RESUMEN
# ==============================
seccion("Resumen Del Módulo")

if modo == "General":
    nota(
        "Se compara el portafolio equiponderado frente al benchmark global para evaluar si realmente agregó valor. El análisis se complementa con tasa libre de riesgo, inflación y tasa de cambio."
    )
else:
    nota(
        "Se evalúa el desempeño relativo del portafolio frente al benchmark mediante retorno acumulado, alpha, tracking error e information ratio, incorporando además variables macro para contextualizar la lectura."
    )

st.markdown(
    f"""
    <div class="bm-meta-row">
        <div class="bm-mini-meta"><strong>Horizonte:</strong>&nbsp;{horizonte}</div>
        <div class="bm-mini-meta"><strong>Inicio:</strong>&nbsp;{start_date}</div>
        <div class="bm-mini-meta"><strong>Fin:</strong>&nbsp;{end_date}</div>
        <div class="bm-mini-meta benchmark-pill"><strong>Benchmark:</strong>&nbsp;{GLOBAL_BENCHMARK}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================
# TABS
# ==============================
tab1, tab2, tab3 = st.tabs([
    "Contexto macro y benchmark",
    "Desempeño relativo",
    "Tablas e interpretación",
])

# ==============================
# TAB 1
# ==============================
with tab1:
    seccion("Indicadores Macroeconómicos")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta_kpi(
            "Tasa libre de riesgo",
            f"{rf_pct:.2f}%" if rf_pct is not None else "N/D",
            help_text="Proviene de macro_snapshot() y se usa como referencia en métricas ajustadas por riesgo.",
            subtexto="Referencia base para comparar retorno frente a riesgo.",
        )

    with c2:
        tarjeta_kpi(
            "Inflación interanual",
            f"{inflation_yoy:.2%}" if inflation_yoy is not None else "N/D",
            delta_label(
                inflation_yoy - 0.05 if inflation_yoy is not None else None,
                "Inflación alta",
                "Inflación moderada",
                "Inflación cercana al umbral"
            ),
            help_text="Variación interanual del nivel general de precios.",
            subtexto="Ayuda a contextualizar el entorno monetario del periodo.",
        )

    with c3:
        fx_delta = None
        if usdcop_market is not None and cop_per_usd is not None:
            if usdcop_market > cop_per_usd:
                fx_delta = "Spot sobre promedio"
            elif usdcop_market < cop_per_usd:
                fx_delta = "Spot bajo promedio"
            else:
                fx_delta = "Spot similar al promedio"

        tarjeta_kpi(
            "USD/COP spot",
            f"{usdcop_market:.2f}" if usdcop_market is not None else "N/D",
            fx_delta,
            help_text="Tasa de cambio observada en el mercado.",
            subtexto="Nivel actual de referencia frente al promedio anual.",
        )

    with c4:
        tarjeta_kpi(
            "USD/COP promedio anual",
            f"{cop_per_usd:.2f}" if cop_per_usd is not None else "N/D",
            help_text="Promedio anual de la tasa de cambio.",
            subtexto="Sirve como referencia para comparar el spot observado.",
        )

    plot_card_footer(interpret_macro_context(rf_pct, inflation_yoy, usdcop_market, cop_per_usd))

    if mostrar_estado_macro:
        with st.expander("Ver estado de carga de variables macro"):
            if inflation_yoy is None:
                st.warning("No se pudo obtener inflación desde API. Se usó fallback o quedó no disponible.")
            if usdcop_market is None:
                st.warning("No se pudo obtener USD/COP spot desde API. Se usó fallback o quedó no disponible.")
            if cop_per_usd is None:
                st.warning("No se pudo obtener USD/COP promedio anual desde API. Se usó fallback o quedó no disponible.")

    seccion("Comparación Visual")

    plot_card_header(
        "Portafolio vs benchmark",
        "El gráfico base 100 permite comparar el desempeño acumulado del portafolio frente al índice de referencia.",
        modo=modo,
        caption="Una línea por encima de la otra sugiere mejor desempeño acumulado relativo.",
    )

    toolbar_label("Opciones de visualización")
    g1, g2 = st.columns(2)
    with g1:
        clean_chart = st.checkbox("Vista limpia", value=False, key="bm_clean_chart")
    with g2:
        show_interpretation_box = st.checkbox("Mostrar guía de lectura", value=True, key="bm_show_chart_guide")

    fig_benchmark = plot_benchmark_base100(cum_port, cum_bench)
    fig_benchmark = style_plot(fig_benchmark, modo)
    fig_benchmark.update_layout(
        title=dict(
            text="Portafolio Vs Benchmark (Base 100)",
            x=0.03,
            xanchor="left",
            y=0.97,
            yanchor="top",
            font=dict(size=16, color="#0F172A"),
        ),
        margin=dict(l=20, r=20, t=70, b=20),
    )
    fig_benchmark.update_xaxes(tickfont=dict(size=12, color="#334155"))
    fig_benchmark.update_yaxes(tickfont=dict(size=12, color="#334155"))

    if clean_chart:
        try:
            fig_benchmark.update_layout(showlegend=False)
        except Exception:
            pass

    st.plotly_chart(fig_benchmark, use_container_width=True)

    if show_interpretation_box:
        if modo == "General":
            plot_card_footer(
                "Si la línea del portafolio termina por encima del benchmark, hubo mejor desempeño acumulado. Si ambas series se mueven de forma muy parecida, el portafolio siguió de cerca al índice. Caídas profundas reflejan episodios de mayor presión de riesgo."
            )
        else:
            plot_card_footer(
                "La separación entre curvas refleja desempeño relativo acumulado. La amplitud de las caídas permite identificar drawdowns y sensibilidad del portafolio frente a choques de mercado."
            )

# ==============================
# TAB 2
# ==============================
with tab2:
    seccion("KPIs De Desempeño Relativo")

    diff_ret = (ret_port - ret_bench) if ret_port is not None and ret_bench is not None else None

    d1, d2, d3, d4 = st.columns(4)

    with d1:
        tarjeta_kpi(
            "Retorno acumulado portafolio",
            f"{ret_port:.2%}" if ret_port is not None else "N/D",
            f"Diferencia: {diff_ret:.2%}" if diff_ret is not None else None,
            help_text="Desempeño acumulado del portafolio en el periodo.",
            subtexto="Resultado agregado de la cartera equiponderada.",
        )

    with d2:
        tarjeta_kpi(
            "Retorno acumulado benchmark",
            f"{ret_bench:.2%}" if ret_bench is not None else "N/D",
            help_text="Desempeño acumulado del benchmark global.",
            subtexto="Punto de referencia para comparar generación de valor.",
        )

    with d3:
        tarjeta_kpi(
            "Alpha de Jensen",
            f"{alpha_jensen:.4f}" if alpha_jensen is not None else "N/D",
            delta_label(alpha_jensen, "Alpha positivo", "Alpha negativo", "Alpha neutro"),
            help_text="Exceso de desempeño ajustado por riesgo sistemático.",
            subtexto="Mide si el portafolio agregó valor frente a lo esperado por CAPM.",
        )

    with d4:
        tarjeta_kpi(
            "Tracking Error",
            f"{tracking_error:.4f}" if tracking_error is not None else "N/D",
            delta_label(
                (0.05 - tracking_error) if tracking_error is not None else None,
                "Desviación moderada",
                "Alta desviación",
                "Desviación límite",
            ),
            help_text="Desviación del portafolio frente al benchmark.",
            subtexto="Cuantifica cuánto se aparta la cartera del índice de referencia.",
        )

    plot_card_footer(interpret_relative_performance(ret_port, ret_bench, alpha_jensen, tracking_error))

    seccion("Métricas Complementarias")

    e1, e2 = st.columns(2)

    with e1:
        tarjeta_kpi(
            "Information Ratio",
            f"{information_ratio:.4f}" if information_ratio is not None else "N/D",
            delta_label(
                information_ratio,
                "Retorno activo eficiente",
                "Retorno activo débil",
                "Lectura neutral",
            ),
            help_text="Retorno activo por unidad de riesgo activo.",
            subtexto="Relaciona generación de valor frente al benchmark con el tracking error.",
        )

    with e2:
        tarjeta_kpi(
            "Máximo drawdown",
            f"{max_drawdown:.2%}" if max_drawdown is not None else "N/D",
            help_text="Peor caída acumulada desde un máximo previo.",
            subtexto="Mide la severidad del peor episodio de pérdida acumulada.",
        )

# ==============================
# TAB 3
# ==============================
with tab3:
    seccion("Tablas De Resultados")

    if mostrar_tablas:
        st.markdown("#### Desempeño: Portafolio vs benchmark")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.markdown("#### Métricas adicionales")
        st.dataframe(extras_df, use_container_width=True, hide_index=True)
    else:
        with st.expander("Ver tablas completas de resultados"):
            st.markdown("#### Desempeño: Portafolio vs benchmark")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            st.markdown("#### Métricas adicionales")
            st.dataframe(extras_df, use_container_width=True, hide_index=True)

    seccion("Interpretación Final")

    if modo == "General":
        nota(
            "El benchmark funciona como punto de comparación para evaluar si el portafolio realmente agregó valor. Un alpha positivo sugiere un desempeño superior al esperado según su riesgo de mercado, mientras que un tracking error alto indica que la cartera se aleja más del índice de referencia."
        )
        nota(
            "La lectura conjunta con inflación, tasa libre de riesgo y tasa de cambio permite entender mejor si el resultado del portafolio ocurrió en un entorno favorable, exigente o volátil."
        )
    else:
        if mostrar_interpretacion_tecnica:
            nota(
                "El análisis relativo frente al benchmark debe leerse de forma conjunta: el retorno acumulado muestra el resultado observado, el alpha de Jensen resume exceso de desempeño ajustado por riesgo sistemático, el tracking error cuantifica riesgo activo, el information ratio mide eficiencia del retorno activo y el máximo drawdown refleja severidad de las pérdidas acumuladas."
            )
            nota(
                "Desde el punto de vista macroeconómico, la tasa libre de riesgo afecta el costo de oportunidad y el cálculo de métricas ajustadas por riesgo, mientras que inflación y tasa de cambio ayudan a contextualizar el entorno financiero en el que se generó el desempeño relativo."
            )