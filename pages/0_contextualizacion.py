# pages/0_contextualizacion.py

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
        label_visibility="collapsed",
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
            key="contexto_activo",
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
        "rol": "Ancla defensiva",
        "aporte": "Consumo básico y estabilidad relativa",
    },
    "Couche-Tard": {
        "nombre": "Alimentation Couche-Tard Inc.",
        "logo": "assets/logos/couche_tard.png",
        "descripcion": "Operador global de tiendas de conveniencia y estaciones de servicio.",
        "pais": "CA · Canadá",
        "ticker": "ATD.TO",
        "rol": "Retail internacional",
        "aporte": "Diversificación geográfica y operativa",
    },
    "FEMSA": {
        "nombre": "Fomento Económico Mexicano, S.A.B. de C.V.",
        "logo": "assets/logos/femsa.png",
        "descripcion": "Conglomerado con operaciones en retail, bebidas y logística.",
        "pais": "MX · México",
        "ticker": "FMX",
        "rol": "Exposición regional",
        "aporte": "Latinoamérica, consumo y estructura diversificada",
    },
    "BP": {
        "nombre": "BP p.l.c.",
        "logo": "assets/logos/bp.png",
        "descripcion": "Empresa energética global con exposición a petróleo, gas y transición energética.",
        "pais": "GB · Reino Unido",
        "ticker": "BP",
        "rol": "Cobertura sectorial",
        "aporte": "Exposición energética y sensibilidad macro",
    },
    "Carrefour": {
        "nombre": "Carrefour S.A.",
        "logo": "assets/logos/carrefour.png",
        "descripcion": "Retail europeo enfocado en supermercados e hipermercados.",
        "pais": "FR · Francia",
        "ticker": "CA.PA",
        "rol": "Retail defensivo europeo",
        "aporte": "Consumo recurrente y diversificación por mercado",
    },
}

# =============================
# ESTILOS LOCALES DEL MÓDULO
# =============================
accent = "#7A1633" if modo == "Estadístico" else "#2563EB"
accent_second = "#A61E46" if modo == "Estadístico" else "#1D4ED8"
accent_soft = "rgba(166, 30, 70, 0.10)" if modo == "Estadístico" else "rgba(37, 99, 235, 0.10)"
accent_border = "rgba(166, 30, 70, 0.18)" if modo == "Estadístico" else "rgba(37, 99, 235, 0.18)"

card_bg = "#FFFFFF"
card_bg_2 = "#F8FBFF" if modo == "General" else "#FFF8FA"
border_soft = "rgba(148, 163, 184, 0.20)"

text_main = "#0F172A"
text_soft = "#334155"
text_muted = "#64748B"

st.markdown(
    f"""
    <style>
    .ctx-kpi {{
        background: linear-gradient(180deg, {card_bg} 0%, {card_bg_2} 100%);
        border: 1px solid {border_soft};
        border-radius: 18px;
        padding: 1rem 1rem 0.95rem 1rem;
        min-height: 126px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 0.75rem;
        transition: all 0.18s ease;
    }}

    .ctx-kpi:hover {{
        transform: translateY(-2px);
        box-shadow: 0 14px 28px rgba(15, 23, 42, 0.10);
        border-color: {accent_border};
    }}

    .ctx-kpi-label {{
        font-size: 0.88rem;
        color: {text_muted} !important;
        font-weight: 800;
        margin-bottom: 0.45rem;
        line-height: 1.25;
    }}

    .ctx-kpi-value {{
        font-size: 1.7rem;
        font-weight: 900;
        color: {text_main} !important;
        line-height: 1.05;
        margin-bottom: 0.35rem;
        letter-spacing: -0.02em;
    }}

    .ctx-kpi-sub {{
        font-size: 0.94rem;
        color: {text_soft} !important;
        line-height: 1.5;
    }}

    .ctx-company {{
        background: linear-gradient(180deg, {card_bg} 0%, {card_bg_2} 100%);
        border: 1px solid {border_soft};
        border-radius: 18px;
        padding: 1rem 1.05rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
    }}

    .ctx-company-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.4rem;
        flex-wrap: wrap;
    }}

    .ctx-badge {{
        display: inline-flex;
        align-items: center;
        font-size: 0.76rem;
        font-weight: 800;
        color: white !important;
        background: linear-gradient(135deg, {accent}, {accent_second});
        border-radius: 999px;
        padding: 0.30rem 0.74rem;
        letter-spacing: 0.02em;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.14);
    }}

    .ctx-company-caption {{
        font-size: 0.84rem;
        color: {text_muted} !important;
        font-weight: 800;
    }}

    .ctx-company-title {{
        font-size: 1.16rem;
        font-weight: 900;
        color: {text_main} !important;
        margin-top: 0.08rem;
        line-height: 1.2;
    }}

    .ctx-company-desc {{
        font-size: 0.94rem;
        color: {text_soft} !important;
        margin-top: 0.35rem;
        margin-bottom: 0.78rem;
        line-height: 1.5;
    }}

    .ctx-meta-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.65rem;
        margin-bottom: 0.75rem;
    }}

    .ctx-meta-card {{
        background: {accent_soft};
        border: 1px solid {accent_border};
        border-radius: 14px;
        padding: 0.72rem 0.82rem;
    }}

    .ctx-meta-label {{
        font-size: 0.78rem;
        color: {text_muted} !important;
        font-weight: 800;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    .ctx-meta-value {{
        font-size: 0.94rem;
        color: {text_main} !important;
        font-weight: 800;
    }}

    .ctx-role-box {{
        background: {accent_soft};
        border-left: 4px solid {accent};
        border-radius: 12px;
        padding: 0.78rem 0.88rem;
        margin-top: 0.1rem;
    }}

    .ctx-role-title {{
        font-size: 0.82rem;
        color: {text_muted} !important;
        font-weight: 800;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    .ctx-role-text {{
        font-size: 0.94rem;
        color: {text_main} !important;
        line-height: 1.5;
    }}

    .ctx-role-text strong {{
        color: {text_main} !important;
    }}

    .ctx-list-card {{
        background: linear-gradient(180deg, {card_bg} 0%, {card_bg_2} 100%);
        border: 1px solid {border_soft};
        border-radius: 16px;
        padding: 0.95rem 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 0.85rem;
        color: {text_soft} !important;
        line-height: 1.7;
    }}

    .ctx-list-card strong {{
        color: {text_main} !important;
    }}

    .ctx-kpi *,
    .ctx-company *,
    .ctx-list-card * {{
        opacity: 1 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# FUNCIONES UI
# =============================
def kpi_box(label: str, value: str, sub: str):
    st.markdown(
        f"""
        <div class="ctx-kpi">
            <div class="ctx-kpi-label">{label}</div>
            <div class="ctx-kpi-value">{value}</div>
            <div class="ctx-kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_empresa(nombre, data, resaltar_rol=False):
    st.markdown('<div class="ctx-company">', unsafe_allow_html=True)

    top_left, top_right = st.columns([7, 2])
    with top_left:
        st.markdown(
            f"""
            <div class="ctx-company-caption">{nombre}</div>
            <div class="ctx-company-title">{data['nombre']}</div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        st.markdown(f'<div class="ctx-badge">{data["ticker"]}</div>', unsafe_allow_html=True)

    logo_col, info_col = st.columns([1.6, 6])

    with logo_col:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(data["logo"], width=200)

    with info_col:
        st.markdown(
            f'<div class="ctx-company-desc">{data["descripcion"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="ctx-meta-grid">
                <div class="ctx-meta-card">
                    <div class="ctx-meta-label">País</div>
                    <div class="ctx-meta-value">{data["pais"]}</div>
                </div>
                <div class="ctx-meta-card">
                    <div class="ctx-meta-label">Ticker</div>
                    <div class="ctx-meta-value">{data["ticker"]}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if resaltar_rol:
            st.markdown(
                f"""
                <div class="ctx-role-box">
                    <div class="ctx-role-title">Rol En El Portafolio</div>
                    <div class="ctx-role-text">
                        <strong>{data["rol"]}:</strong> {data["aporte"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


# =============================
# HEADER
# =============================
header_dashboard(
    "Contextualización Del Portafolio",
    "Comprende el rol estratégico, la composición y la lógica económica del portafolio",
    modo=modo,
)

if modo == "General":
    nota("Este módulo resume por qué estos activos conviven en el portafolio y qué papel cumple cada empresa dentro de la estrategia global.")
else:
    nota("En modo estadístico, la contextualización funciona como marco interpretativo para leer después rendimientos, volatilidad, riesgo extremo y optimización.")

# =============================
# RESUMEN GENERAL
# =============================
seccion("Estructura Del Portafolio")

titulo_con_ayuda(
    "Perfil General",
    "Describe la lógica global del portafolio y su exposición al riesgo."
)

if expandir:
    k1, k2, k3 = st.columns(3)

    with k1:
        kpi_box("Número De Activos", "5", "Portafolio concentrado pero diversificado por empresa y región.")
    with k2:
        kpi_box("Sectores Dominantes", "Retail + Energía", "Combinación entre consumo defensivo y sensibilidad macro.")
    with k3:
        kpi_box("Cobertura Geográfica", "América / Europa / Asia", "Diversificación internacional con exposición multinacional.")

if mostrar_lectura:
    st.markdown(
        """
        <div class="ctx-list-card">
            - Portafolio diversificado entre retail defensivo y energía.<br>
            - Exposición a consumo recurrente, operación internacional y factores macroeconómicos.<br>
            - Combinación de activos con perfiles diferentes para enriquecer el análisis de riesgo y diversificación.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================
# EMPRESAS DEL PORTAFOLIO
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

    st.markdown(
        """
        <div class="ctx-list-card">
            - <strong>Técnico:</strong> estudia señales visuales del precio y momentum.<br>
            - <strong>Rendimientos:</strong> analiza retornos, dispersión y comportamiento temporal.<br>
            - <strong>GARCH:</strong> modela la volatilidad condicional del portafolio o de cada activo.<br>
            - <strong>CAPM:</strong> evalúa riesgo sistemático y sensibilidad frente al mercado.<br>
            - <strong>VaR / CVaR:</strong> cuantifica riesgo extremo y pérdidas potenciales.<br>
            - <strong>Markowitz:</strong> conecta la contextualización con la lógica de diversificación y optimización.
        </div>
        """,
        unsafe_allow_html=True,
    )