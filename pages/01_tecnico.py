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
    titulo_con_ayuda,
    tarjeta_kpi,
    nota,
)

from ui.dashboard_filters import ayuda_contextual

ensure_project_dirs()

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
    "Explora tendencia, momentum y señales técnicas del activo seleccionado"
)

nota("Este módulo permite analizar el comportamiento del activo mediante indicadores técnicos clave.")

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
    nota(f"Vista General Del Comportamiento De {asset_name} ({ticker}).")
else:
    ayuda_contextual(
        "Interpretación Técnica",
        "Se Utilizan Indicadores Para Evaluar Tendencia, Dispersión Y Momentum Del Activo."
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
    tarjeta_kpi(
        "Precio",
        f"{close_now:,.2f}" if close_now is not None else "N/D",
        f"{delta:.2%}" if delta is not None else "",
        help_text="Último Precio De Cierre Disponible Para El Activo En El Periodo Consultado."
    )

with c2:
    tarjeta_kpi(
        "RSI",
        f"{rsi_now:.2f}" if rsi_now is not None else "N/D",
        help_text="El RSI Mide Momentum. Valores Altos Pueden Sugerir Sobrecompra Y Valores Bajos Sobreventa."
    )

with c3:
    tarjeta_kpi(
        "SMA",
        f"{sma_now:.2f}" if sma_now is not None else "N/D",
        help_text="La SMA Es Una Media Móvil Simple Que Suaviza El Precio Y Ayuda A Identificar Tendencia."
    )

with c4:
    tarjeta_kpi(
        "EMA",
        f"{ema_now:.2f}" if ema_now is not None else "N/D",
        help_text="La EMA Da Más Peso A Los Datos Recientes Y Reacciona Más Rápido A Cambios Del Precio."
    )

# ==============================
# GRÁFICO PRINCIPAL
# ==============================
seccion("Tendencia Del Precio")

titulo_con_ayuda(
    "Precio Con Medias Móviles",
    "Compara El Precio Del Activo Con La SMA Y La EMA Para Evaluar Tendencia Y Detectar Posibles Cambios Recientes.",
)

st.plotly_chart(
    plot_price_and_mas(ind, sma_col=f"SMA_{sma_window}", ema_col=f"EMA_{ema_window}"),
    use_container_width=True
)

# ==============================
# INDICADORES
# ==============================
seccion("Indicadores")

col1, col2 = st.columns(2)

with col1:
    titulo_con_ayuda(
        "RSI",
        "El RSI Mide La Fuerza Relativa Del Movimiento Del Precio. Valores Cercanos A 70 Pueden Sugerir Sobrecompra Y Cercanos A 30, Sobreventa.",
    )
    st.plotly_chart(
        plot_rsi(ind, rsi_col=f"RSI_{rsi_window}"),
        use_container_width=True
    )

with col2:
    titulo_con_ayuda(
        "Bandas De Bollinger",
        "Las Bandas Muestran Dispersión Alrededor De La Media Móvil. Su Expansión Suele Asociarse Con Mayor Volatilidad Y Su Contracción Con Menor Volatilidad.",
    )
    st.plotly_chart(
        plot_bollinger(ind),
        use_container_width=True
    )

# ==============================
# AVANZADOS
# ==============================
if modo == "Estadístico":
    seccion("Indicadores Avanzados")

    col3, col4 = st.columns(2)

    with col3:
        titulo_con_ayuda(
            "MACD",
            "El MACD Ayuda A Identificar Cambios De Momentum Mediante La Diferencia Entre Medias Exponenciales Y Sus Cruces Con La Línea De Señal.",
        )
        st.plotly_chart(
            plot_macd(ind),
            use_container_width=True
        )

    with col4:
        titulo_con_ayuda(
            "Oscilador Estocástico",
            "Compara El Cierre Actual Con El Rango Reciente Del Precio Para Detectar Zonas Extremas Y Posibles Cambios De Dirección.",
        )
        st.plotly_chart(
            plot_stochastic(ind),
            use_container_width=True
        )

# ==============================
# TABLA
# ==============================
seccion("Datos Recientes")

with st.expander("Ver Tabla"):
    st.dataframe(ind.tail(15), use_container_width=True)