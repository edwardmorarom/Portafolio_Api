from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from arch import arch_model


def _scale_returns(log_returns: pd.Series) -> pd.Series:
    """
    Escala por 100 para estabilidad numérica.
    """
    return 100 * log_returns.dropna()


def fit_garch_models(log_returns: pd.Series) -> dict:
    """
    Ajusta ARCH(1), GARCH(1,1) y EGARCH(1,1).
    Devuelve resultados serializables.
    """
    r = _scale_returns(log_returns)
    if len(r) < 100:
        return {
            "comparison": pd.DataFrame(),
            "volatility": pd.DataFrame(),
            "forecast": pd.DataFrame(),
            "diagnostics": pd.DataFrame(),
        }

    specs = {
        "ARCH(1)": arch_model(r, mean="Constant", vol="ARCH", p=1, q=0, dist="normal"),
        "GARCH(1,1)": arch_model(r, mean="Constant", vol="GARCH", p=1, q=1, dist="normal"),
        "EGARCH(1,1)": arch_model(r, mean="Constant", vol="EGARCH", p=1, q=1, dist="normal"),
    }

    comparison_rows = []
    vol_dict = {}
    fitted_results = {}

    for name, model in specs.items():
        res = model.fit(disp="off")
        fitted_results[name] = res
        comparison_rows.append(
            {
                "modelo": name,
                "loglik": res.loglikelihood,
                "AIC": res.aic,
                "BIC": res.bic,
            }
        )
        vol = pd.Series(res.conditional_volatility, index=r.index, name=name)
        vol_dict[name] = vol

    comparison = pd.DataFrame(comparison_rows).sort_values("AIC").reset_index(drop=True)
    best_model_name = comparison.iloc[0]["modelo"]
    best_result = fitted_results[best_model_name]

    forecast = best_result.forecast(horizon=10)
    forecast_var = forecast.variance.iloc[-1]
    forecast_df = pd.DataFrame(
        {
            "horizonte": list(range(1, len(forecast_var) + 1)),
            "varianza_pronosticada": forecast_var.values,
            "volatilidad_pronosticada": np.sqrt(forecast_var.values),
        }
    )

    std_resid = pd.Series(best_result.std_resid, index=r.index).dropna()
    jb = stats.jarque_bera(std_resid)

    diagnostics = pd.DataFrame(
        {
            "metrica": [
                "modelo_seleccionado",
                "jb_residuos_stat",
                "jb_residuos_pvalue",
            ],
            "valor": [
                best_model_name,
                jb.statistic,
                jb.pvalue,
            ],
        }
    )
    diagnostics["valor"] = diagnostics["valor"].astype(str)

    vol_df = pd.concat(vol_dict.values(), axis=1)

    return {
        "comparison": comparison,
        "volatility": vol_df,
        "forecast": forecast_df,
        "diagnostics": diagnostics,
        "best_model_name": best_model_name,
        "std_resid": std_resid.to_frame("std_resid"),
    }
