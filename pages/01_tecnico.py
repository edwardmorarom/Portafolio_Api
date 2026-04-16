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
    header_dashboard,
    seccion,
    titulo_con_ayuda,
    tarjeta_kpi,
    nota,
)

from ui.dashboard_filters import (
    selector_modo,
    ayuda_contextual,
)

ensure_project_dirs()

# ==============================
# ESTILOS GLOBALES
# ==============================
aplicar_estilos_globales()

# ==============================
# HEADER
# ==============================
header_dashboard(
    "Módulo 1 - Análisis técnico",
    "Explora tendencia, momentum y señales técnicas del activo seleccionado"
)

nota("Este módulo permite analizar el comportamiento del activo mediante indicadores técnicos clave.")

# ==============================
# FILTROS
# ==============================
with st.container():
    st.markdown("""
    <div style="
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
    ">
    """, unsafe_allow_html=True)

    st.markdown("### Configuración del análisis")
    st.caption("Selecciona el modo y ajusta los parámetros del análisis técnico.")

    modo = selector_modo()

    col1, col2 = st.columns(2)

    with col1:
        asset_name = st.selectbox("Activo", list(ASSETS.keys()))

    with col2:
        horizonte = st.selectbox(
            "Horizonte",
            ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
            index=3
        )

    with st.expander("⚙️ Parámetros técnicos avanzados"):
        sma_window = st.slider("Ventana SMA", 5, 60, 20, key="tec_sma")
        ema_window = st.slider("Ventana EMA", 5, 60, 20, key="tec_ema")
        rsi_window = st.slider("Ventana RSI", 5, 30, 14, key="tec_rsi")
        bb_window = st.slider("Bollinger", 10, 60, 20, key="tec_bb")
        stoch_window = st.slider("Estocástico", 5, 30, 14, key="tec_stoch")

    st.markdown("</div>", unsafe_allow_html=True)

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
        start_date = st.date_input("Fecha inicial", DEFAULT_START_DATE, key="tec_fecha_inicial")
    with fecha_col2:
        end_date = st.date_input("Fecha final", DEFAULT_END_DATE, key="tec_fecha_final")

# ==============================
# DATOS
# ==============================
ticker = get_ticker(asset_name)
df = download_single_ticker(ticker, str(start_date), str(end_date))

if df.empty:
    st.error("No se pudieron descargar datos.")
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
    st.error("No fue posible calcular indicadores técnicos.")
    st.stop()

# ==============================
# RESUMEN
# ==============================
seccion("Resumen")

if modo == "General":
    nota(f"Vista general del comportamiento de {asset_name} ({ticker}).")
else:
    ayuda_contextual(
        "Interpretación técnica",
        "Se utilizan indicadores para evaluar tendencia, dispersión y momentum del activo."
    )

# ==============================
# KPIs
# ==============================
seccion("KPIs del activo")

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
        help_text="Último precio de cierre disponible para el activo en el periodo consultado."
    )

with c2:
    tarjeta_kpi(
        "RSI",
        f"{rsi_now:.2f}" if rsi_now is not None else "N/D",
        help_text="El RSI mide momentum. Valores altos pueden sugerir sobrecompra y valores bajos sobreventa."
    )

with c3:
    tarjeta_kpi(
        "SMA",
        f"{sma_now:.2f}" if sma_now is not None else "N/D",
        help_text="La SMA es una media móvil simple que suaviza el precio y ayuda a identificar tendencia."
    )

with c4:
    tarjeta_kpi(
        "EMA",
        f"{ema_now:.2f}" if ema_now is not None else "N/D",
        help_text="La EMA da más peso a los datos recientes y reacciona más rápido a cambios del precio."
    )

# ==============================
# GRÁFICO PRINCIPAL
# ==============================
seccion("Tendencia del precio")

titulo_con_ayuda(
    "Precio con medias móviles",
    "Compara el precio del activo con la SMA y la EMA para evaluar tendencia y detectar posibles cambios recientes.",
    nivel=3
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
        "El RSI mide la fuerza relativa del movimiento del precio. Valores cercanos a 70 pueden sugerir sobrecompra y cercanos a 30, sobreventa.",
        nivel=3
    )
    st.plotly_chart(
        plot_rsi(ind, rsi_col=f"RSI_{rsi_window}"),
        use_container_width=True
    )

with col2:
    titulo_con_ayuda(
        "Bandas de Bollinger",
        "Las bandas muestran dispersión alrededor de la media móvil. Su expansión suele asociarse con mayor volatilidad y su contracción con menor volatilidad.",
        nivel=3
    )
    st.plotly_chart(
        plot_bollinger(ind),
        use_container_width=True
    )

# ==============================
# AVANZADOS
# ==============================
if modo == "Estadístico":
    seccion("Indicadores avanzados")

    col3, col4 = st.columns(2)

    with col3:
        titulo_con_ayuda(
            "MACD",
            "El MACD ayuda a identificar cambios de momentum mediante la diferencia entre medias exponenciales y sus cruces con la línea de señal.",
            nivel=3
        )
        st.plotly_chart(
            plot_macd(ind),
            use_container_width=True
        )

    with col4:
        titulo_con_ayuda(
            "Oscilador estocástico",
            "Compara el cierre actual con el rango reciente del precio para detectar zonas extremas y posibles cambios de dirección.",
            nivel=3
        )
        st.plotly_chart(
            plot_stochastic(ind),
            use_container_width=True
        )

# ==============================
# TABLA
# ==============================
seccion("Datos recientes")

with st.expander("Ver tabla"):
    st.dataframe(ind.tail(15), use_container_width=True)