import streamlit as st


def contenedor_filtros(titulo: str = "Filtros del panel", descripcion: str = ""):
    descripcion_html = f"<p style='margin-top:0.35rem; color:#cbd5e1;'>{descripcion}</p>" if descripcion else ""

    st.markdown(f"""
    <div style="
        background: rgba(15,23,42,0.82);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 16px;
        padding: 1rem 1rem 0.8rem 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 6px 22px rgba(0,0,0,0.18);
    ">
        <div style="
            font-size:1.05rem;
            font-weight:700;
            color:#f8fafc;
            margin-bottom:0.2rem;
        ">{titulo}</div>
        {descripcion_html}
    </div>
    """, unsafe_allow_html=True)


def selector_modo(key: str = "modo_dashboard", default: str = "General"):
    opciones = ["General", "Estadístico"]
    index_default = opciones.index(default) if default in opciones else 0

    modo = st.radio(
        "Modo de visualización",
        options=opciones,
        index=index_default,
        horizontal=True,
        key=key,
        help="General muestra una vista ejecutiva y resumida. Estadístico muestra métricas y lectura técnica más detallada."
    )
    return modo


def filtros_generales(
    activos,
    categorias=None,
    key_prefix: str = "filtros_generales"
):
    if categorias is None:
        categorias = []

    col1, col2, col3 = st.columns(3)

    with col1:
        activo = st.selectbox(
            "Activo",
            options=["Todos"] + list(activos),
            key=f"{key_prefix}_activo",
            help="Selecciona un activo puntual o deja 'Todos' para una vista agregada."
        )

    with col2:
        categoria = st.selectbox(
            "Categoría",
            options=["Todas"] + list(categorias),
            key=f"{key_prefix}_categoria",
            help="Permite segmentar por grupo o tipo de activo."
        )

    with col3:
        horizonte = st.selectbox(
            "Horizonte",
            options=["1 mes", "3 meses", "6 meses", "1 año"],
            index=1,
            key=f"{key_prefix}_horizonte",
            help="Define el periodo sobre el cual se visualiza el análisis."
        )

    return {
        "activo": activo,
        "categoria": categoria,
        "horizonte": horizonte,
    }


def filtros_estadisticos(key_prefix: str = "filtros_estadisticos"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metrica = st.selectbox(
            "Métrica",
            options=["Rentabilidad", "Volatilidad", "Sharpe", "Drawdown"],
            key=f"{key_prefix}_metrica",
            help="Selecciona la métrica principal para el análisis técnico."
        )

    with col2:
        ventana = st.selectbox(
            "Ventana",
            options=["30 días", "60 días", "90 días", "180 días"],
            index=2,
            key=f"{key_prefix}_ventana",
            help="Tamaño de la ventana de observación usada para el cálculo."
        )

    with col3:
        normalizar = st.toggle(
            "Normalizar datos",
            value=False,
            key=f"{key_prefix}_normalizar",
            help="Escala los datos para facilitar la comparación entre series."
        )

    with col4:
        outliers = st.toggle(
            "Mostrar outliers",
            value=True,
            key=f"{key_prefix}_outliers",
            help="Permite visualizar valores extremos dentro del análisis."
        )

    return {
        "metrica": metrica,
        "ventana": ventana,
        "normalizar": normalizar,
        "outliers": outliers,
    }


def ayuda_contextual(titulo: str, texto: str):
    with st.expander(f"ℹ️ {titulo}", expanded=False):
        st.markdown(texto)


def bloque_informativo(label: str, descripcion: str):
    st.markdown(f"""
    <div style="
        background: rgba(30,41,59,0.65);
        border: 1px solid rgba(148,163,184,0.10);
        border-radius: 14px;
        padding: 0.85rem;
        margin-bottom: 0.75rem;
    ">
        <div style="
            font-weight:700;
            color:#f8fafc;
            margin-bottom:0.35rem;
        ">{label}</div>
        <div style="
            font-size:0.92rem;
            color:#cbd5e1;
            line-height:1.45;
        ">{descripcion}</div>
    </div>
    """, unsafe_allow_html=True)


def grid_ayudas(items: list[tuple[str, str]]):
    if not items:
        return

    cols = st.columns(len(items))
    for col, (titulo, descripcion) in zip(cols, items):
        with col:
            bloque_informativo(titulo, descripcion)