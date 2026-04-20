import streamlit as st
import pandas as pd

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, get_ticker, ensure_project_dirs
from src.download import download_single_ticker
from src.indicators import compute_all_indicators
from src.plots import (
    plot_price_and_mas,
    plot_bollinger,
    plot_rsi,
    plot_macd,
    plot_stochastic,
)

from ui.dashboard_ui import (
    aplicar_estilos_globales,
    render_sidebar_brand,
    render_sidebar_panel,
    header_dashboard,
    seccion,
    nota,
    plot_card_header,
    plot_card_footer,
    toolbar_label,
)

from ui.dashboard_filters import ayuda_contextual

ensure_project_dirs()


def inject_tecnico_styles(modo: str):
    accent = "#9F1239" if modo == "Estadístico" else "#2563EB"
    accent_second = "#BE123C" if modo == "Estadístico" else "#1D4ED8"
    accent_soft = "rgba(190, 24, 93, 0.10)" if modo == "Estadístico" else "rgba(37, 99, 235, 0.10)"
    accent_border = "rgba(190, 24, 93, 0.20)" if modo == "Estadístico" else "rgba(37, 99, 235, 0.20)"
    panel_bg_2 = "#FFF7F9" if modo == "Estadístico" else "#F8FBFF"

    st.markdown(
        f"""
        <style>
        .tec-kpi-card {{
            background: linear-gradient(180deg, #ffffff 0%, {panel_bg_2} 100%);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 18px;
            padding: 0.95rem 1rem 0.95rem 1rem;
            min-height: 124px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            transition: all 0.18s ease;
            position: relative;
            overflow: hidden;
        }}

        .tec-kpi-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, {accent}, {accent_second});
        }}

        .tec-kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.10);
            border-color: {accent_border};
        }}

        .tec-kpi-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.5rem;
            margin-bottom: 0.65rem;
        }}

        .tec-kpi-label {{
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 900;
            color: #64748B !important;
            line-height: 1.2;
        }}

        .tec-kpi-help {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            font-size: 0.72rem;
            font-weight: 800;
            color: {accent} !important;
            background: {accent_soft};
            border: 1px solid {accent_border};
            flex-shrink: 0;
            cursor: help;
        }}

        .tec-kpi-value {{
            font-size: 1.85rem;
            font-weight: 900;
            color: #0F172A !important;
            line-height: 1.05;
            margin-bottom: 0.3rem;
            letter-spacing: -0.02em;
        }}

        .tec-kpi-delta {{
            font-size: 0.84rem;
            font-weight: 800;
            line-height: 1.3;
        }}

        .tec-kpi-delta.pos {{
            color: #16A34A !important;
        }}

        .tec-kpi-delta.neg {{
            color: #DC2626 !important;
        }}

        .tec-kpi-delta.neu {{
            color: #475569 !important;
        }}

        .tec-kpi-sub {{
            font-size: 0.88rem;
            color: #475569 !important;
            line-height: 1.45;
            margin-top: 0.2rem;
        }}

        .tec-kpi-card * {{
            opacity: 1 !important;
        }}

        .ui-mode-badge,
        .ui-mode-badge *,
        .ui-plot-head .ui-mode-badge,
        .ui-plot-head .ui-mode-badge * {{
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            opacity: 1 !important;
            font-weight: 900 !important;
        }}

        div[data-testid="stPlotlyChart"] .js-plotly-plot .plotly .legend text {{
            fill: #334155 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_tecnico(titulo: str, valor: str, delta: str = "", subtexto: str = "", help_text: str = ""):
    delta_class = "neu"
    if delta.startswith("+"):
        delta_class = "pos"
    elif delta.startswith("-"):
        delta_class = "neg"

    help_html = f'<span class="tec-kpi-help" title="{help_text}">?</span>' if help_text else ""

    st.markdown(
        f"""
        <div class="tec-kpi-card">
            <div class="tec-kpi-top">
                <div class="tec-kpi-label">{titulo}</div>
                {help_html}
            </div>
            <div class="tec-kpi-value">{valor}</div>
            <div class="tec-kpi-delta {delta_class}">{delta}</div>
            <div class="tec-kpi-sub">{subtexto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def apply_trace_visibility(fig, visibility_map: dict):
    for trace in fig.data:
        trace_name = str(getattr(trace, "name", "") or "").lower()

        for keywords, should_show in visibility_map.items():
            if any(keyword in trace_name for keyword in keywords):
                trace.visible = True if should_show else "legendonly"
                break

    return fig


def find_column_by_groups(df: pd.DataFrame, groups: list[tuple[str, ...]]):
    columns = list(df.columns)
    for group in groups:
        for col in columns:
            col_l = col.lower()
            if all(token in col_l for token in group):
                return col
    return None


def interpret_trend(close_now, sma_now, ema_now):
    if close_now is None:
        return "No hay suficiente información para interpretar la tendencia actual."

    if sma_now is None or ema_now is None:
        return "La lectura visual sugiere revisar el precio junto con las medias móviles para confirmar la tendencia."

    if close_now > sma_now and close_now > ema_now:
        return "El precio se mantiene por encima de la SMA y la EMA, lo que sugiere una tendencia reciente con sesgo alcista."
    if close_now < sma_now and close_now < ema_now:
        return "El precio se ubica por debajo de la SMA y la EMA, señal compatible con debilidad relativa en el periodo analizado."
    return "El precio está cerca de las medias móviles, lo que sugiere una zona de transición o consolidación."


def interpret_rsi(rsi_now):
    if rsi_now is None:
        return "No fue posible calcular una lectura actual del RSI."

    if rsi_now >= 70:
        return f"RSI en {rsi_now:.2f}: el activo se encuentra en zona de sobrecompra relativa."
    if rsi_now <= 30:
        return f"RSI en {rsi_now:.2f}: el activo se encuentra en zona de sobreventa relativa."
    return f"RSI en {rsi_now:.2f}: el momentum es intermedio y no muestra una señal extrema."


def interpret_bollinger(ind: pd.DataFrame, close_now):
    upper_col = find_column_by_groups(
        ind,
        [
            ("bb", "upper"),
            ("boll", "upper"),
            ("upper", "band"),
        ],
    )
    lower_col = find_column_by_groups(
        ind,
        [
            ("bb", "lower"),
            ("boll", "lower"),
            ("lower", "band"),
        ],
    )

    if close_now is None or upper_col is None or lower_col is None:
        return "Observa la posición del precio frente a las bandas para identificar episodios de alta o baja dispersión."

    upper_now = ind[upper_col].iloc[-1]
    lower_now = ind[lower_col].iloc[-1]

    if pd.notna(upper_now) and close_now > upper_now:
        return "El precio se ubica por encima de la banda superior, señal típica de presión alcista intensa o posible agotamiento."
    if pd.notna(lower_now) and close_now < lower_now:
        return "El precio se ubica por debajo de la banda inferior, lo que puede sugerir presión bajista intensa o eventual rebote técnico."

    return "El precio se mantiene dentro del canal de Bollinger, sin ruptura extrema de dispersión."


def interpret_macd():
    return "Evalúa los cruces entre MACD y señal junto con el histograma para detectar aceleración o pérdida de momentum."


def interpret_stochastic():
    return "Usa %K y %D para identificar zonas extremas y posibles cambios de dirección en horizontes cortos."


# ==============================
# ESTILOS + SIDEBAR
# ==============================
aplicar_estilos_globales()

render_sidebar_brand(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    logo_path="assets/escudo_santo_tomas.png",
)

modo, filtros_sidebar = render_sidebar_panel(
    modo_default="General",
    filtros_label="Parámetros Técnicos Avanzados",
    filtros_expanded=False,
)

aplicar_estilos_globales(modo=modo)
inject_tecnico_styles(modo)

with filtros_sidebar:
    asset_name = st.selectbox("Activo", list(ASSETS.keys()), key="tec_asset")

    horizonte = st.selectbox(
        "Horizonte",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="tec_horizonte",
    )

    sma_window = st.slider("Ventana SMA", 5, 60, 20, key="tec_sma")
    ema_window = st.slider("Ventana EMA", 5, 60, 20, key="tec_ema")
    rsi_window = st.slider("Ventana RSI", 5, 30, 14, key="tec_rsi")
    bb_window = st.slider("Bollinger", 10, 60, 20, key="tec_bb")
    stoch_window = st.slider("Estocástico", 5, 30, 14, key="tec_stoch")

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 1 - Análisis técnico",
    "Explora tendencia, momentum y señales técnicas del activo seleccionado",
    modo=modo,
)

if modo == "General":
    nota("Vista ejecutiva del comportamiento técnico del activo. Usa los filtros sobre cada gráfico para decidir qué series quieres observar.")
else:
    nota("Vista técnica ampliada con énfasis en momentum, dispersión y señales de confirmación. El entorno cambia a vinotinto para diferenciar claramente el modo estadístico.")

# ==============================
# FECHAS
# ==============================
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
    fecha_col1, fecha_col2 = st.columns(2)
    with fecha_col1:
        start_date = st.date_input("Fecha Inicial", DEFAULT_START_DATE, key="tec_fecha_inicial")
    with fecha_col2:
        end_date = st.date_input("Fecha Final", DEFAULT_END_DATE, key="tec_fecha_final")

# ==============================
# DATOS
# ==============================
ticker = get_ticker(asset_name)
df = download_single_ticker(ticker, str(start_date), str(end_date))

if df.empty:
    st.error("No Se Pudieron Descargar Datos.")
    st.stop()

ind = compute_all_indicators(
    df,
    sma_window=sma_window,
    ema_window=ema_window,
    rsi_window=rsi_window,
    bb_window=bb_window,
    stoch_window=stoch_window,
)

if ind.empty:
    st.error("No Fue Posible Calcular Indicadores Técnicos.")
    st.stop()

# ==============================
# RESUMEN
# ==============================
seccion("Resumen")

if modo == "General":
    nota(f"Vista general del comportamiento de {asset_name} ({ticker}) en el horizonte seleccionado.")
else:
    ayuda_contextual(
        "Interpretación Técnica",
        "Se utilizan indicadores para evaluar tendencia, dispersión y momentum del activo."
    )

# ==============================
# KPIs
# ==============================
seccion("KPIs Del Activo")

close_now = float(ind["Close"].iloc[-1]) if "Close" in ind.columns else None
close_prev = float(ind["Close"].iloc[-2]) if "Close" in ind.columns and len(ind) > 1 else None
rsi_now = float(ind[f"RSI_{rsi_window}"].iloc[-1]) if f"RSI_{rsi_window}" in ind.columns else None
sma_now = float(ind[f"SMA_{sma_window}"].iloc[-1]) if f"SMA_{sma_window}" in ind.columns else None
ema_now = float(ind[f"EMA_{ema_window}"].iloc[-1]) if f"EMA_{ema_window}" in ind.columns else None

delta = None
if close_now is not None and close_prev is not None and close_prev != 0:
    delta = (close_now / close_prev) - 1

c1, c2, c3, c4 = st.columns(4)

with c1:
    kpi_tecnico(
        "Precio",
        f"{close_now:,.2f}" if close_now is not None else "N/D",
        f"{delta:+.2%}" if delta is not None else "",
        "Último cierre disponible del activo.",
        help_text="Último precio de cierre disponible para el activo en el periodo consultado.",
    )

with c2:
    kpi_tecnico(
        "RSI",
        f"{rsi_now:.2f}" if rsi_now is not None else "N/D",
        "",
        "Momentum relativo del activo.",
        help_text="El RSI mide momentum. Valores altos pueden sugerir sobrecompra y valores bajos sobreventa.",
    )

with c3:
    kpi_tecnico(
        "SMA",
        f"{sma_now:.2f}" if sma_now is not None else "N/D",
        "",
        "Media móvil simple del periodo.",
        help_text="La SMA suaviza el precio y ayuda a identificar tendencia.",
    )

with c4:
    kpi_tecnico(
        "EMA",
        f"{ema_now:.2f}" if ema_now is not None else "N/D",
        "",
        "Media móvil con más peso reciente.",
        help_text="La EMA reacciona más rápido a cambios recientes del precio.",
    )

# ==============================
# GRÁFICO PRINCIPAL
# ==============================
seccion("Tendencia Del Precio")
plot_card_header(
    "Precio con medias móviles",
    "Compara el precio del activo con la SMA y la EMA para evaluar tendencia y detectar posibles cambios recientes.",
    modo=modo,
    caption="Filtros rápidos del gráfico: activa o desactiva series directamente encima de la visualización.",
)

toolbar_label("Series visibles")
p1, p2, p3 = st.columns(3)
with p1:
    show_price = st.checkbox("Precio", value=True, key="tec_show_price")
with p2:
    show_sma = st.checkbox("SMA", value=True, key="tec_show_sma")
with p3:
    show_ema = st.checkbox("EMA", value=True, key="tec_show_ema")

fig_price = plot_price_and_mas(ind, sma_col=f"SMA_{sma_window}", ema_col=f"EMA_{ema_window}")
fig_price = apply_trace_visibility(
    fig_price,
    {
        ("price", "precio", "close", "cierre"): show_price,
        ("sma",): show_sma,
        ("ema",): show_ema,
    },
)
fig_price = style_plot(fig_price, modo)
st.plotly_chart(fig_price, use_container_width=True)
plot_card_footer(interpret_trend(close_now, sma_now, ema_now))

# ==============================
# INDICADORES
# ==============================
seccion("Indicadores")

col1, col2 = st.columns(2)

with col1:
    plot_card_header(
        "RSI",
        "El RSI mide la fuerza relativa del movimiento del precio. Valores cercanos a 70 pueden sugerir sobrecompra y cercanos a 30, sobreventa.",
        modo=modo,
        caption="Controla si deseas una lectura más limpia del oscilador o conservar referencias visuales.",
    )

    toolbar_label("Capas del gráfico")
    r1, r2 = st.columns(2)
    with r1:
        show_rsi_line = st.checkbox("Línea RSI", value=True, key="tec_show_rsi")
    with r2:
        show_rsi_levels = st.checkbox("Niveles 30/70", value=True, key="tec_show_rsi_levels")

    fig_rsi = plot_rsi(ind, rsi_col=f"RSI_{rsi_window}")
    fig_rsi = apply_trace_visibility(
        fig_rsi,
        {
            ("rsi",): show_rsi_line,
            ("70", "30", "sobrecompra", "sobreventa", "upper", "lower"): show_rsi_levels,
        },
    )
    fig_rsi = style_plot(fig_rsi, modo)
    st.plotly_chart(fig_rsi, use_container_width=True)
    plot_card_footer(interpret_rsi(rsi_now))

with col2:
    plot_card_header(
        "Bandas de Bollinger",
        "Las bandas muestran dispersión alrededor de la media móvil. Su expansión suele asociarse con mayor volatilidad y su contracción con menor volatilidad.",
        modo=modo,
        caption="Puedes decidir si observar solo el precio o comparar contra la media y las bandas.",
    )

    toolbar_label("Capas del gráfico")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        show_bb_price = st.checkbox("Precio", value=True, key="tec_show_bb_price")
    with b2:
        show_bb_mean = st.checkbox("Media", value=True, key="tec_show_bb_mean")
    with b3:
        show_bb_upper = st.checkbox("Banda sup.", value=True, key="tec_show_bb_upper")
    with b4:
        show_bb_lower = st.checkbox("Banda inf.", value=True, key="tec_show_bb_lower")

    fig_bb = plot_bollinger(ind)
    fig_bb = apply_trace_visibility(
        fig_bb,
        {
            ("price", "precio", "close", "cierre"): show_bb_price,
            ("sma", "middle", "media", "mean", "basis"): show_bb_mean,
            ("upper", "superior", "sup"): show_bb_upper,
            ("lower", "inferior", "inf"): show_bb_lower,
        },
    )
    fig_bb = style_plot(fig_bb, modo)
    st.plotly_chart(fig_bb, use_container_width=True)
    plot_card_footer(interpret_bollinger(ind, close_now))

# ==============================
# AVANZADOS
# ==============================
if modo == "Estadístico":
    seccion("Indicadores Avanzados")

    col3, col4 = st.columns(2)

    with col3:
        plot_card_header(
            "MACD",
            "El MACD ayuda a identificar cambios de momentum mediante la diferencia entre medias exponenciales y sus cruces con la línea de señal.",
            modo=modo,
            caption="En modo estadístico se habilitan indicadores complementarios para lectura técnica más fina.",
        )

        toolbar_label("Capas del gráfico")
        m1, m2, m3 = st.columns(3)
        with m1:
            show_macd = st.checkbox("MACD", value=True, key="tec_show_macd")
        with m2:
            show_signal = st.checkbox("Señal", value=True, key="tec_show_signal")
        with m3:
            show_hist = st.checkbox("Histograma", value=True, key="tec_show_hist")

        fig_macd = plot_macd(ind)
        fig_macd = apply_trace_visibility(
            fig_macd,
            {
                ("macd",): show_macd,
                ("signal", "señal", "signal line"): show_signal,
                ("hist", "histogram"): show_hist,
            },
        )
        fig_macd = style_plot(fig_macd, modo)
        st.plotly_chart(fig_macd, use_container_width=True)
        plot_card_footer(interpret_macd())

    with col4:
        plot_card_header(
            "Oscilador Estocástico",
            "Compara el cierre actual con el rango reciente del precio para detectar zonas extremas y posibles cambios de dirección.",
            modo=modo,
            caption="Activa o desactiva %K y %D según la lectura que quieras priorizar.",
        )

        toolbar_label("Capas del gráfico")
        s1, s2 = st.columns(2)
        with s1:
            show_k = st.checkbox("%K", value=True, key="tec_show_k")
        with s2:
            show_d = st.checkbox("%D", value=True, key="tec_show_d")

        fig_stoch = plot_stochastic(ind)
        fig_stoch = apply_trace_visibility(
            fig_stoch,
            {
                ("%k", "k", "fast"): show_k,
                ("%d", "d", "slow"): show_d,
            },
        )
        fig_stoch = style_plot(fig_stoch, modo)
        st.plotly_chart(fig_stoch, use_container_width=True)
        plot_card_footer(interpret_stochastic())

# ==============================
# TABLA
# ==============================
seccion("Datos Recientes")

with st.expander("Ver Tabla"):
    st.dataframe(ind.tail(15), use_container_width=True)