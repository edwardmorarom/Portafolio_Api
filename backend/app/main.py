# uvicorn backend.app.main:app --reload

from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import pandas as pd

from src.risk_metrics import (
    parametric_var_cvar,
    historical_var_cvar,
    risk_comparison_table,
)

app = FastAPI(title="Risk API", version="1.0")


class ReturnsInput(BaseModel):
    returns: list[float]
    alpha: float = 0.95


class CompareInput(BaseModel):
    returns: list[float]
    alpha: float = 0.95


class PortfolioInput(BaseModel):
    returns: list[list[float]]  # filas = tiempo, columnas = activos
    weights: list[float]
    alpha: float = 0.95


@app.get("/")
def root():
    return {"message": "API de riesgo funcionando"}


@app.post("/var/parametric")
def compute_parametric_var(data: ReturnsInput):
    try:
        returns_series = pd.Series(data.returns).astype(float)
        result = parametric_var_cvar(returns_series, alpha=data.alpha)

        if not result:
            return {"error": "La función no devolvió resultados válidos"}

        result_clean = {k: float(v) for k, v in result.items()}
        return result_clean

    except Exception as e:
        return {"error": str(e)}


@app.post("/var/historical")
def compute_historical_var(data: ReturnsInput):
    try:
        returns_series = pd.Series(data.returns).astype(float)
        result = historical_var_cvar(returns_series, alpha=data.alpha)

        if not result:
            return {"error": "La función no devolvió resultados válidos"}

        result_clean = {k: float(v) for k, v in result.items()}
        return result_clean

    except Exception as e:
        return {"error": str(e)}


@app.post("/var/compare")
def compare_var_methods(data: CompareInput):
    try:
        returns_series = pd.Series(data.returns).astype(float)

        comparison_df = risk_comparison_table(
            portfolio_returns=returns_series,
            asset_returns_df=pd.DataFrame({"asset": returns_series}),
            weights=[1.0],
            alpha=data.alpha,
            n_sim=10000,
        )

        if comparison_df.empty:
            return {"error": "No fue posible construir la tabla comparativa"}

        # Convertir a tipos serializables
        records = comparison_df.to_dict(orient="records")
        records_clean = []
        for row in records:
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, (np.floating, np.integer)):
                    clean_row[k] = float(v)
                else:
                    clean_row[k] = v
            records_clean.append(clean_row)

        return records_clean

    except Exception as e:
        return {"error": str(e)}


@app.post("/portfolio/var")
def compute_portfolio_var(data: PortfolioInput):
    try:
        returns_df = pd.DataFrame(data.returns).astype(float)
        weights = pd.Series(data.weights, dtype=float)

        if returns_df.empty:
            return {"error": "La matriz de retornos está vacía"}

        if len(weights) != returns_df.shape[1]:
            return {"error": "Dimensión de pesos no coincide con activos"}

        if not np.isclose(weights.sum(), 1.0, atol=1e-6):
            return {"error": "Los pesos deben sumar 1"}

        # 🔥 Construcción del portafolio
        portfolio_returns = returns_df.dot(weights)
        portfolio_returns = pd.Series(portfolio_returns).dropna()

        if len(portfolio_returns) < 10:
            return {"error": "Muy pocos datos para calcular VaR"}

        # 🔥 Cálculo directo (robusto)
        mu = portfolio_returns.mean()
        sigma = portfolio_returns.std(ddof=1)

        if np.isclose(sigma, 0):
            return {"error": "Varianza cero"}

        from scipy.stats import norm

        z = norm.ppf(1 - data.alpha)

        var_diario = -(mu + z * sigma)
        cvar_diario = -(mu + (norm.pdf(z) / (1 - data.alpha)) * sigma)

        var_anual = var_diario * np.sqrt(252)
        cvar_anual = cvar_diario * np.sqrt(252)

        return {
            "weights": weights.tolist(),
            "n_obs": int(len(portfolio_returns)),
            "portfolio_var": {
                "VaR_diario": float(var_diario),
                "CVaR_diario": float(cvar_diario),
                "VaR_anualizado": float(var_anual),
                "CVaR_anualizado": float(cvar_anual),
            },
        }

    except Exception as e:
        return {"error": str(e)}