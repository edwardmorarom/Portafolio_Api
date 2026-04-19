import streamlit as st
from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import (
    header_dashboard,
    seccion,
    titulo_con_ayuda,
    nota,
)

# =============================
# SETUP GLOBAL
# =============================
modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
)

# =============================
# CONFIGURACIÓN FILTROS
# =============================
with filtros_sidebar:
    st.markdown("### Vista Del Módulo")

    vista = st.radio(
        "Vista",
        ["Vista Resumida", "Un Activo", "Todos Los Activos"],
        key="contexto_vista",
        label_visibility="collapsed"
    )

    activo = None
    if vista == "Un Activo":
        activo = st.selectbox(
            "Selecciona Activo",
            [
                "Seven & i Holdings",
                "Couche-Tard",
                "FEMSA",
                "BP",
                "Carrefour",
            ],
            key="contexto_activo"
        )

    st.markdown("---")

    mostrar_lectura = st.checkbox("Mostrar Lectura General Del Portafolio", True)
    expandir = st.checkbox("Expandir Resumen General", True)
    resaltar = st.checkbox("Resaltar Rol En Portafolio", True)
    conexion = st.checkbox("Mostrar Conexión Con Módulos", True)


# =============================
# DATA EMPRESAS
# =============================
empresas = {
    "Seven & i Holdings": {
        "nombre": "Seven & i Holdings Co., Ltd.",
        "logo": "assets/logos/seven_i.png",
        "descripcion": "Retail diversificado con fuerte presencia en tiendas de conveniencia (7-Eleven).",
        "pais": "JP · Japón",
        "ticker": "3382.T",
    },
    "Couche-Tard": {
        "nombre": "Alimentation Couche-Tard Inc.",
        "logo": "assets/logos/couche_tard.png",
        "descripcion": "Operador global de tiendas de conveniencia y estaciones de servicio.",
        "pais": "CA · Canadá",
        "ticker": "ATD.TO",
    },
    "FEMSA": {
        "nombre": "Fomento Económico Mexicano, S.A.B. de C.V.",
        "logo": "assets/logos/femsa.png",
        "descripcion": "Conglomerado con operaciones en retail, bebidas y logística.",
        "pais": "MX · México",
        "ticker": "FMX",
    },
    "BP": {
        "nombre": "BP p.l.c.",
        "logo": "assets/logos/bp.png",
        "descripcion": "Empresa energética global con exposición a petróleo, gas y transición energética.",
        "pais": "GB · Reino Unido",
        "ticker": "BP",
    },
    "Carrefour": {
        "nombre": "Carrefour S.A.",
        "logo": "assets/logos/carrefour.png",
        "descripcion": "Retail europeo enfocado en supermercados e hipermercados.",
        "pais": "FR · Francia",
        "ticker": "CA.PA",
    },
}


# =============================
# FUNCIÓN TARJETA
# =============================
def card_empresa(nombre, data, resaltar_rol=False):
    with st.container():
        st.markdown("""
        <div style="
            background: rgba(9, 20, 43, 0.92);
            border: 1px solid rgba(148,163,184,0.14);
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        ">
        """, unsafe_allow_html=True)

        col_logo, col_info = st.columns([1, 8])

        with col_logo:
            st.image(data["logo"], width=160)

        with col_info:
            st.markdown(
                f"<div style='font-size:0.88rem; color:#93a4bf;'>{nombre}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:1.18rem; font-weight:800; color:#f8fafc;'>{data['nombre']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:0.92rem; color:#cbd5e1; margin-top:4px;'>{data['descripcion']}</div>",
                unsafe_allow_html=True,
            )

            meta1, meta2 = st.columns(2)
            with meta1:
                st.markdown(
                    f"<div style='font-size:0.88rem; color:#93a4bf; margin-top:8px;'>País</div>"
                    f"<div style='font-size:0.95rem; font-weight:600; color:#e5e7eb;'>{data['pais']}</div>",
                    unsafe_allow_html=True,
                )
            with meta2:
                st.markdown(
                    f"<div style='font-size:0.88rem; color:#93a4bf; margin-top:8px;'>Ticker</div>"
                    f"<div style='font-size:0.95rem; font-weight:600; color:#e5e7eb;'>{data['ticker']}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)


# =============================
# HEADER
# =============================
header_dashboard(
    "Contextualización Del Portafolio",
    "Comprende El Rol Estratégico, Composición Y Lógica Económica Del Portafolio"
)

nota("Este módulo proporciona una visión integral del portafolio y su lógica de construcción.")

# =============================
# CONTENIDO
# =============================
seccion("Estructura Del Portafolio")

titulo_con_ayuda(
    "Perfil General",
    "Describe la lógica global del portafolio y su exposición al riesgo"
)

if mostrar_lectura:
    st.markdown("""
- Portafolio diversificado en retail y energía
- Exposición a consumo defensivo
- Sensibilidad a ciclos macroeconómicos
""")


# =============================
# VISTA DINÁMICA
# =============================
seccion("Empresas Del Portafolio")

if vista == "Vista Resumida":
    for nombre, data in empresas.items():
        card_empresa(nombre, data, resaltar)

elif vista == "Un Activo":
    if activo:
        card_empresa(activo, empresas[activo], resaltar)

elif vista == "Todos Los Activos":
    cols = st.columns(2)
    items = list(empresas.items())

    for i, (nombre, data) in enumerate(items):
        with cols[i % 2]:
            card_empresa(nombre, data, resaltar)


# =============================
# CONEXIÓN CON OTROS MÓDULOS
# =============================
if conexion:
    seccion("Relación Con Otros Módulos")

    st.markdown("""
- **Técnico:** comportamiento del precio
- **Rendimientos:** análisis de retornos
- **GARCH:** volatilidad
- **CAPM:** riesgo sistemático
- **VaR / CVaR:** riesgo extremo
- **Markowitz:** optimización
""")