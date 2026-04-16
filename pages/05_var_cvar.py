import streamlit as st
import numpy as np
import pandas as pd

from src.config import ASSETS, DEFAULT_START_DATE, DEFAULT_END_DATE, ensure_project_dirs
from src.download import load_market_bundle
from src.preprocess import equal_weight_vector, equal_weight_portfolio
from src.risk_metrics import risk_comparison_table, kupiec_test
from src.plots import plot_var_distribution

ensure_project_dirs()

st.title("Módulo 5 - VaR y CVaR")
st.caption(
    "Evalúa el riesgo extremo del portafolio mediante VaR y CVaR bajo distintos enfoques de estimación."
)

# ==============================
# Sidebar
# ==============================
with st.sidebar:
    st.header("Parámetros de riesgo")

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
        start_date = st.date_input("Fecha inicial", value=DEFAULT_START_DATE, key="var_start")
        end_date = st.date_input("Fecha final", value=DEFAULT_END_DATE, key="var_end")

    alpha = st.selectbox("Nivel de confianza", [0.95, 0.99], index=0)

    st.divider()
    st.subheader("Modo de visualización")
    modo = st.radio(
        "Selecciona el nivel de detalle",
        ["General", "Estadístico"],
        index=0,
    )

    st.divider()
    st.subheader("Opciones de visualización")
    mostrar_tablas = st.checkbox("Mostrar tablas completas", value=False)
    mostrar_backtesting = st.checkbox("Mostrar backtesting", value=True)

    mostrar_fundamento = False
    mostrar_interpretacion_tecnica = False
    mostrar_simulacion = False

    if modo == "Estadístico":
        mostrar_fundamento = st.checkbox("Mostrar fundamento teórico", value=False)
        mostrar_interpretacion_tecnica = st.checkbox("Mostrar interpretación técnica", value=True)

        with st.expander("Filtros secundarios"):
            n_sim = st.slider(
                "Simulaciones Monte Carlo",
                min_value=5000,
                max_value=50000,
                value=10000,
                step=5000,
            )
    else:
        n_sim = 10000

# ==============================
# Carga y preparación de datos
# ==============================
tickers = [meta["ticker"] for meta in ASSETS.values()]
bundle = load_market_bundle(tickers=tickers, start=str(start_date), end=str(end_date))
returns = bundle["returns"].replace([np.inf, -np.inf], np.nan).dropna()

if returns.empty or len(returns) < 30:
    st.error("No hay suficientes datos para calcular métricas de riesgo.")
    st.stop()

weights = equal_weight_vector(returns.shape[1])
portfolio_returns = equal_weight_portfolio(returns)

table = risk_comparison_table(
    portfolio_returns=portfolio_returns,
    asset_returns_df=returns,
    weights=weights,
    alpha=alpha,
    n_sim=n_sim,
)

if table.empty:
    st.error("No fue posible calcular VaR y CVaR con los datos disponibles.")
    st.stop()

# ==============================
# Resumen
# ==============================
st.markdown("### Resumen del módulo")
if modo == "General":
    st.write(
        f"""
        Este módulo estima cuánto podría perder el portafolio en escenarios adversos con un nivel de confianza
        del **{int(alpha * 100)}%**. El VaR muestra una pérdida umbral, mientras que el CVaR muestra qué tan
        severas serían, en promedio, las pérdidas más extremas.
        """
    )
else:
    st.write(
        f"""
        Este módulo compara el **Value at Risk (VaR)** y el **Conditional Value at Risk (CVaR)** del portafolio
        equiponderado bajo enfoques **paramétrico**, **histórico** y **Monte Carlo**, usando la convención de
        pérdidas positivas para un nivel de confianza de **{int(alpha * 100)}%**.
        """
    )

st.caption(f"Periodo analizado: {start_date} a {end_date}")

# ==============================
# Fundamento teórico
# ==============================
if modo == "Estadístico" and mostrar_fundamento:
    st.markdown("### Fundamento teórico")

    st.markdown(
        rf"""
        Sea $R_{{p,t}}$ el rendimiento del portafolio en el periodo \(t\), definido como combinación lineal
        de los rendimientos de los activos según sus pesos. En este análisis, la pérdida se define como:
        """
    )
    st.latex(r"L_t = -R_{p,t}")

    st.markdown(
        r"""
        De esta forma:

        - valores **positivos** de \(L_t\) representan **pérdidas**
        - valores **negativos** de \(L_t\) representan **ganancias**

        El **Value at Risk (VaR)** al nivel de confianza \(\alpha\) corresponde al cuantil de la distribución
        de pérdidas. En términos prácticos, representa la pérdida máxima esperada que no se excede con
        probabilidad \(\alpha\).

        El **Conditional Value at Risk (CVaR)**, también llamado **Expected Shortfall**, mide la pérdida promedio
        en los escenarios más extremos, es decir, cuando la pérdida supera el VaR.

        **Convención usada en este proyecto:**
        - El **VaR** y el **CVaR** se reportan como **pérdidas positivas**.
        - Por ejemplo, un VaR diario de **0.025** significa una pérdida potencial de **2.5%**.
        """
    )

    st.info(
        """
        **Interpretación de métodos**
        - **Paramétrico**: supone normalidad de los rendimientos del portafolio.
        - **Histórico**: usa la distribución empírica observada, sin imponer una distribución teórica.
        - **Monte Carlo**: simula escenarios futuros a partir de la media y la matriz de covarianza de los activos.
        """
    )

# ==============================
# Portafolio
# ==============================
st.markdown("### Portafolio analizado")
if modo == "General":
    st.write("Se usa un portafolio equiponderado, es decir, todos los activos tienen el mismo peso.")
else:
    with st.expander("Ver pesos del portafolio"):
        pesos_df = pd.DataFrame({
            "Activo": returns.columns,
            "Peso": weights,
        })
        st.dataframe(pesos_df, width="stretch")

# ==============================
# Filas por método
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
# KPIs
# ==============================
st.markdown("### KPIs de riesgo")

col1, col2, col3, col4 = st.columns(4)
col1.metric(f"VaR histórico {int(alpha * 100)}%", f"{var_h:.2%}" if var_h is not None else "N/D")
col2.metric(f"CVaR histórico {int(alpha * 100)}%", f"{cvar_h:.2%}" if cvar_h is not None else "N/D")
col3.metric("VaR paramétrico", f"{var_p:.2%}" if var_p is not None else "N/D")
col4.metric("VaR Monte Carlo", f"{var_mc:.2%}" if var_mc is not None else "N/D")

# ==============================
# Gráfico
# ==============================
st.markdown("### Distribución y riesgo extremo")
st.caption(
    "El histograma muestra la distribución de rendimientos. Las líneas punteadas representan VaR y CVaR por método."
)
st.plotly_chart(plot_var_distribution(portfolio_returns, table), width="stretch")

if modo == "General":
    st.info(
        """
        **Cómo leer este gráfico**

        - El histograma resume cómo se distribuyen los rendimientos del portafolio.
        - Las líneas de **VaR** marcan pérdidas umbral bajo distintos métodos.
        - Las líneas de **CVaR** muestran pérdidas promedio más severas en escenarios extremos.
        - Cuando el CVaR es más alto que el VaR, significa que las pérdidas extremas pueden ser considerablemente más intensas.
        """
    )
else:
    with st.expander("Ver interpretación técnica del gráfico"):
        st.write(
            """
            El gráfico permite contrastar la distribución empírica del portafolio con los umbrales de VaR y CVaR
            obtenidos bajo distintos enfoques. La separación entre líneas ayuda a comparar conservadurismo,
            sensibilidad al riesgo extremo y coherencia entre métricas de cola.
            """
        )

# ==============================
# Tabla
# ==============================
st.markdown("### Comparación VaR / CVaR")
if mostrar_tablas:
    st.dataframe(table, width="stretch")
else:
    with st.expander("Ver tabla completa de VaR y CVaR"):
        st.dataframe(table, width="stretch")

# ==============================
# Interpretación
# ==============================
st.markdown("### Interpretación")

lectura_simple = f"""
**Lectura sencilla**

- Con {int(alpha * 100)}% de confianza, la pérdida diaria del portafolio no superaría aproximadamente **{var_h:.2%}**.
- Si ocurre un evento extremo que supera ese umbral, la pérdida promedio podría acercarse a **{cvar_h:.2%}**.
- El CVaR es más severo que el VaR porque se enfoca en los peores escenarios.
"""

interpretacion_tecnica = []

if var_h is not None and cvar_h is not None:
    interpretacion_tecnica.append(
        f"Con {int(alpha * 100)}% de confianza, el **VaR histórico diario** del portafolio es **{var_h:.2%}**, "
        f"mientras que el **CVaR histórico diario** es **{cvar_h:.2%}**."
    )
    interpretacion_tecnica.append(
        "Esto implica que, en escenarios de pérdida extrema, el promedio de pérdidas severas supera el umbral del VaR, "
        "lo cual es consistente con la interpretación del CVaR como medida más sensible al riesgo de cola."
    )

if var_p is not None and var_h is not None:
    if var_p < var_h:
        interpretacion_tecnica.append(
            "El VaR paramétrico es menor que el VaR histórico, lo que puede sugerir que el supuesto de normalidad "
            "subestima el riesgo extremo frente a la evidencia empírica."
        )
    elif var_p > var_h:
        interpretacion_tecnica.append(
            "El VaR paramétrico es mayor que el VaR histórico, lo que sugiere una estimación más conservadora "
            "bajo el supuesto normal."
        )
    else:
        interpretacion_tecnica.append(
            "El VaR paramétrico y el VaR histórico son muy similares para esta muestra."
        )

if var_mc is not None:
    interpretacion_tecnica.append(
        f"El **VaR Monte Carlo diario** estimado es **{var_mc:.2%}**, útil para contrastar "
        "la sensibilidad del riesgo ante simulaciones probabilísticas."
    )

st.success(lectura_simple)

tab1, tab2 = st.tabs(["Interpretación por métodos", "Advertencia metodológica"])

with tab1:
    for msg in interpretacion_tecnica:
        st.write(f"- {msg}")

with tab2:
    st.warning(
        "El VaR paramétrico depende del supuesto de normalidad. Si la distribución de rendimientos presenta colas pesadas "
        "o asimetría, este método puede subestimar el riesgo extremo."
    )

with st.expander("Ver interpretación técnica completa"):
    st.write(
        """
        El VaR resume una pérdida umbral bajo un nivel de confianza dado, mientras que el CVaR
        captura la pérdida promedio cuando ese umbral ya fue superado. Por eso el CVaR ofrece una
        lectura más sensible del riesgo extremo.

        La comparación entre enfoque histórico, paramétrico y Monte Carlo permite evaluar si el riesgo
        estimado depende fuertemente de supuestos distribucionales o de simulación.
        """
    )
    for msg in interpretacion_tecnica:
        st.write(f"- {msg}")

# ==============================
# Backtesting VaR - Test de Kupiec
# ==============================
if mostrar_backtesting:
    st.markdown("### Backtesting VaR - Test de Kupiec")

    if var_h is not None:
        kupiec = kupiec_test(
            returns=portfolio_returns,
            var=var_h,
            alpha=alpha,
        )

        if kupiec:
            col1, col2, col3 = st.columns(3)
            col1.metric("Violaciones", kupiec["violations"])
            col2.metric("Observadas (%)", f"{kupiec['observed_fail_rate'] * 100:.2f}%")
            col3.metric("Esperadas (%)", f"{kupiec['expected_fail_rate'] * 100:.2f}%")

            st.write(f"**p-value:** {kupiec['p_value']:.4f}")
            st.write(f"**Conclusión:** {kupiec['conclusion']}")

            if kupiec["p_value"] > 0.05:
                st.success(
                    "El VaR histórico es consistente con la frecuencia de pérdidas observadas en la muestra."
                )
            else:
                st.error(
                    "El VaR histórico no es consistente con la frecuencia de pérdidas observadas. "
                    "Esto sugiere que el modelo puede estar subestimando o sobreestimando el riesgo."
                )

            if modo == "Estadístico":
                with st.expander("Ver explicación del test de Kupiec"):
                    st.info(
                        "El test de Kupiec compara la proporción esperada de violaciones del VaR con la proporción observada. "
                        "Es una forma de evaluar si el modelo de riesgo está calibrado de manera razonable."
                    )
            else:
                st.info(
                    "Este bloque verifica si el VaR estimado fue razonable frente a las pérdidas realmente observadas."
                )
        else:
            st.warning("No se pudo ejecutar el test de Kupiec.")
    else:
        st.warning("No hay VaR histórico disponible para ejecutar el test de Kupiec.")