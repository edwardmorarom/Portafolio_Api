
# Dashboard de Gestión de Portafolios y Teoría del Riesgo

Aplicación desarrollada en **Python** y **Streamlit** para el análisis de un portafolio internacional de activos financieros. El proyecto integra datos históricos de mercado y variables macroeconómicas para evaluar rendimiento, riesgo, volatilidad, optimización y señales de decisión.

## Descripción

Este dashboard permite estudiar un portafolio compuesto por cinco activos internacionales mediante herramientas de análisis financiero y estadístico. La aplicación descarga datos desde APIs, construye métricas de riesgo y rendimiento, compara el portafolio frente a benchmarks y presenta los resultados en una interfaz interactiva.

El sistema fue construido con una arquitectura modular, donde cada componente del análisis está separado en archivos independientes dentro de `src/` y cada vista del dashboard se implementa en `pages/`.

## Objetivo

Desarrollar una herramienta interactiva para apoyar el análisis de portafolios desde la perspectiva de la teoría del riesgo, integrando:

- análisis técnico,
- rendimientos y estadística descriptiva,
- modelos ARCH/GARCH,
- CAPM,
- VaR y CVaR,
- optimización de Markowitz,
- señales automáticas,
- contexto macroeconómico y benchmark.

## Activos del portafolio

| Empresa | Ticker | Mercado |
|---|---|---|
| Seven & i Holdings | `3382.T` | Japón |
| Alimentation Couche-Tard | `ATD.TO` | Canadá |
| FEMSA | `FEMSAUBD.MX` | México |
| BP | `BP.L` | Reino Unido |
| Carrefour | `CA.PA` | Francia |

### Benchmark global
- `ACWI`

### Benchmarks locales usados en CAPM
- Seven & i Holdings → `^N225`
- Alimentation Couche-Tard → `^GSPTSE`
- FEMSA → `^MXX`
- BP → `^FTSE`
- Carrefour → `^FCHI`

## Tecnologías utilizadas

- Python
- Streamlit
- pandas
- numpy
- scipy
- plotly
- yfinance
- arch
- requests
- python-dotenv

## Estructura del proyecto

```text
riesgo_dashboard/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── pages/
│   ├── 01_tecnico.py
│   ├── 02_rendimientos.py
│   ├── 03_garch.py
│   ├── 04_capm.py
│   ├── 05_var_cvar.py
│   ├── 06_markowitz.py
│   ├── 07_senales.py
│   └── 08_macro_benchmark.py
│
├── src/
│   ├── benchmark.py
│   ├── capm.py
│   ├── config.py
│   ├── download.py
│   ├── garch_models.py
│   ├── indicators.py
│   ├── macro.py
│   ├── markowitz.py
│   ├── plots.py
│   ├── preprocess.py
│   ├── returns_analysis.py
│   ├── risk_metrics.py
│   └── signals.py
│
├── data/
│   ├── raw/
│   └── processed/
│
└── report/
    └── informe_articulo.tex
````

## Módulos del dashboard

### 1. Análisis técnico

Visualiza precios, medias móviles, RSI, MACD, Bandas de Bollinger y oscilador estocástico.

### 2. Rendimientos

Calcula rendimientos simples y logarítmicos, además de estadísticas descriptivas y comportamiento acumulado.

### 3. Modelos GARCH

Permite analizar la volatilidad condicional mediante modelos ARCH/GARCH.

### 4. CAPM

Estima beta, alpha y retorno esperado del activo respecto a su benchmark.

### 5. VaR y CVaR

Calcula métricas de riesgo extremo mediante distintos enfoques.

### 6. Markowitz

Simula portafolios, construye la frontera eficiente y obtiene portafolios de mínima varianza y máximo Sharpe.

### 7. Señales y alertas

Genera recomendaciones automáticas de compra, venta o mantener a partir de indicadores técnicos.

### 8. Macro y benchmark

Integra variables macroeconómicas desde FRED y compara el portafolio frente al benchmark global.

## Flujo general del sistema

```text
config -> download -> preprocess -> análisis/métricas -> visualización -> páginas del dashboard
```

## Fuentes de datos

### Yahoo Finance

Se utiliza para descargar precios históricos de los activos y benchmarks.

### FRED

Se utiliza para obtener variables macroeconómicas:

* `DGS3MO` → tasa libre de riesgo
* `CPIAUCSL` → inflación
* `COLCCUSMA02STM` → tipo de cambio COP/USD

## Requisitos

* Python 3.10 o superior
* Conexión a internet
* API key de FRED para habilitar el módulo macroeconómico

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/MariaAmaya12/Portafolio_Api.git
cd Portafolio_Api
```

### 2. Crear y activar entorno virtual

#### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Configuración

Crea un archivo `.env` a partir de `.env.example`.

Ejemplo:

```env
FRED_API_KEY=tu_api_key_real
DEFAULT_START_DATE=2021-01-01
DEFAULT_END_DATE=2026-03-27
```

### Nota

Si `FRED_API_KEY` no está definida o es inválida, el módulo macro puede mostrar valores como `N/D`.

## Ejecución

Con el entorno virtual activado, ejecuta:

```bash
python -m streamlit run app.py
```

Luego abre en el navegador:

```text
http://localhost:8501
```

## Estado del proyecto

El proyecto se encuentra en una versión funcional y validada localmente. Actualmente:

* el dashboard corre correctamente en Streamlit,
* la descarga de precios funciona con Yahoo Finance,
* el módulo macro funciona con FRED cuando la API key es válida,
* los módulos CAPM, VaR/CVaR, Markowitz y señales fueron corregidos y probados,
* la estructura modular del proyecto ya está organizada para mantenimiento y extensión.

## Consideraciones importantes

* No subas el archivo `.env` al repositorio.
* No publiques claves API en commits ni capturas.
* Como se usan activos de distintos mercados, algunas fechas pueden no coincidir entre series.
* Si una API externa no responde, algunos módulos pueden mostrar datos incompletos o `N/D`.

## Autor

Proyecto académico desarrollado para el curso de **Teoría del Riesgo**, enfocado en análisis financiero, métricas de riesgo y visualización interactiva de portafolios.

````

