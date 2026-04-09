import streamlit as st

from src.config import ASSETS, GLOBAL_BENCHMARK, ensure_project_dirs

ensure_project_dirs()
st.title("Contextualización de activos")
st.caption("Resumen cualitativo de cada activo del portafolio y su papel dentro del análisis.")

ASSET_CONTEXT = {
    "Seven & i Holdings": {
        "sector": "Retail de conveniencia",
        "resumen": (
            "Holding japonés con exposición al comercio minorista y foco en formatos "
            "de conveniencia. Dentro del portafolio aporta exposición a consumo defensivo "
            "en Asia."
        ),
        "tesis": [
            "Exposición a consumo recurrente y retail defensivo.",
            "Diversificación geográfica hacia Japón.",
            "Activo útil para comparar retail de conveniencia frente a otros mercados."
        ],
        "riesgos": [
            "Presión sobre márgenes del retail.",
            "Desaceleración del consumo en Japón.",
            "Mayor competencia en formatos de proximidad."
        ],
        "catalizadores": [
            "Mejoras operativas.",
            "Resultados trimestrales sólidos.",
            "Fortalecimiento del negocio principal de conveniencia."
        ],
        "rol_portafolio": "Activo defensivo ligado al consumo minorista en Asia.",
    },
    "Alimentation Couche-Tard": {
        "sector": "Convenience & mobility",
        "resumen": (
            "Compañía canadiense enfocada en tiendas de conveniencia y movilidad. "
            "Dentro del portafolio representa exposición a consumo de proximidad y "
            "servicios asociados al tráfico vial."
        ),
        "tesis": [
            "Exposición a un operador global con presencia internacional.",
            "Negocio ligado a conveniencia y movilidad, con flujo operativo recurrente.",
            "Aporta diversificación respecto a mercados emergentes y Europa."
        ],
        "riesgos": [
            "Dependencia del tráfico y entorno de consumo.",
            "Presión de costos operativos.",
            "Sensibilidad del negocio asociado a combustibles y movilidad."
        ],
        "catalizadores": [
            "Expansión internacional.",
            "Mejoras en eficiencia y ventas comparables.",
            "Resultados favorables del negocio minorista y de movilidad."
        ],
        "rol_portafolio": "Activo de consumo y movilidad con exposición a Norteamérica.",
    },
    "FEMSA": {
        "sector": "Bebidas, retail y logística",
        "resumen": (
            "Empresa mexicana con presencia en bebidas, retail y logística. "
            "En el portafolio aporta exposición a Latinoamérica y a negocios "
            "diversificados ligados al consumo."
        ),
        "tesis": [
            "Exposición a una compañía diversificada en segmentos defensivos.",
            "Representa el componente latinoamericano del portafolio.",
            "Combina consumo, distribución y operación regional."
        ],
        "riesgos": [
            "Riesgo cambiario y macroeconómico regional.",
            "Sensibilidad al entorno de consumo en Latinoamérica.",
            "Presión de costos y márgenes en retail y distribución."
        ],
        "catalizadores": [
            "Crecimiento operativo en retail.",
            "Fortaleza de negocios vinculados a bebidas y distribución.",
            "Mejora del entorno macro regional."
        ],
        "rol_portafolio": "Activo latinoamericano con perfil diversificado y exposición a consumo.",
    },
    "BP": {
        "sector": "Energía",
        "resumen": (
            "Compañía energética integrada con exposición a la cadena de valor del sector. "
            "En el portafolio aporta sensibilidad al ciclo energético y diversificación "
            "sectorial frente a retail y consumo."
        ),
        "tesis": [
            "Exposición directa al sector energía.",
            "Diversificación frente a los activos de retail y consumo.",
            "Sensibilidad a variables globales como petróleo, gas y entorno macro."
        ],
        "riesgos": [
            "Alta sensibilidad a precios de energía.",
            "Riesgo regulatorio y geopolítico.",
            "Volatilidad por cambios en estrategia e inversión."
        ],
        "catalizadores": [
            "Recuperación de precios energéticos.",
            "Mejoras en eficiencia y resultados.",
            "Noticias favorables sobre estrategia y portafolio de negocios."
        ],
        "rol_portafolio": "Activo cíclico que introduce exposición energética global.",
    },
    "Carrefour": {
        "sector": "Retail alimentario",
        "resumen": (
            "Grupo francés de distribución alimentaria y retail. "
            "Dentro del portafolio aporta exposición a consumo básico en Europa "
            "y complementa el bloque defensivo del análisis."
        ),
        "tesis": [
            "Exposición a retail alimentario y consumo básico.",
            "Diversificación europea dentro del portafolio.",
            "Comparación interesante frente a otros formatos de retail del portafolio."
        ],
        "riesgos": [
            "Presión competitiva en distribución minorista.",
            "Sensibilidad de márgenes a inflación de costos.",
            "Entorno de consumo débil en Europa."
        ],
        "catalizadores": [
            "Mejoras operativas y eficiencia comercial.",
            "Recuperación del consumo.",
            "Resultados favorables en ventas comparables."
        ],
        "rol_portafolio": "Activo defensivo europeo enfocado en distribución alimentaria.",
    },
}


def render_asset_card(asset_name: str, meta: dict, ctx: dict) -> None:
    st.subheader(f"{asset_name} ({meta['ticker']})")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ticker", meta["ticker"])
    c2.metric("País", meta["country"])
    c3.metric("Benchmark local", meta["benchmark_local"])
    c4.metric("Benchmark global", GLOBAL_BENCHMARK)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Perfil general", "Tesis de inversión", "Riesgos y catalizadores", "Rol en portafolio"]
    )

    with tab1:
        st.markdown(f"**Sector:** {ctx['sector']}")
        st.write(ctx["resumen"])

    with tab2:
        st.markdown("**Puntos clave:**")
        for item in ctx["tesis"]:
            st.write(f"- {item}")

    with tab3:
        col_risk, col_cat = st.columns(2)

        with col_risk:
            st.markdown("**Riesgos principales**")
            for item in ctx["riesgos"]:
                st.write(f"- {item}")

        with col_cat:
            st.markdown("**Catalizadores potenciales**")
            for item in ctx["catalizadores"]:
                st.write(f"- {item}")

    with tab4:
        st.info(ctx["rol_portafolio"])
        st.markdown(
            f"""
**Lectura dentro del dashboard**
- Se compara contra el benchmark local **{meta['benchmark_local']}** en el módulo CAPM.
- Forma parte del portafolio global que luego se contrasta con **{GLOBAL_BENCHMARK}**.
- Su comportamiento también afecta módulos como VaR/CVaR, Markowitz y señales.
"""
        )


with st.sidebar:
    st.header("Configuración")
    modo = st.radio("Vista", ["Un activo", "Todos los activos"], index=0)

asset_names = list(ASSETS.keys())

if modo == "Un activo":
    selected_asset = st.selectbox("Selecciona un activo", asset_names)
    render_asset_card(
        selected_asset,
        ASSETS[selected_asset],
        ASSET_CONTEXT[selected_asset],
    )
else:
    for asset_name in asset_names:
        render_asset_card(
            asset_name,
            ASSETS[asset_name],
            ASSET_CONTEXT[asset_name],
        )
        st.divider()