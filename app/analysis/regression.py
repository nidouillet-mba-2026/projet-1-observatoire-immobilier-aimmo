"""
Fonctions de régression linéaire pour l'analyse immobilière.

Aucune dépendance Streamlit — 100 % testable avec pytest sans lancer l'UI.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import DVF_REGRESSION


# ── Primitives OLS ───────────────────────────────────────────────────────────────

def least_squares_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Régression OLS univariée y ~ x.  Retourne (slope, intercept)."""
    x_mean, y_mean = x.mean(), y.mean()
    denom = float(((x - x_mean) ** 2).sum())
    if denom == 0:
        return 0.0, float(y_mean)
    slope     = float(((x - x_mean) * (y - y_mean)).sum() / denom)
    intercept = float(y_mean - slope * x_mean)
    return slope, intercept


def r_squared(x: np.ndarray, y: np.ndarray, slope: float, intercept: float) -> float:
    """Coefficient de détermination R² = 1 − SS_res / SS_tot."""
    y_pred = slope * x + intercept
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 0.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot


def compute_regression(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Régression linéaire prix ~ surface par type de bien (pure pandas, sans numpy/scipy).

    Enrichit le DataFrame avec :
      - prix_predit    : prix attendu selon la droite de régression
      - ecart          : prix réel − prix prédit  (négatif = sous-évalué)
      - ecart_pct      : écart en % du prix prédit
      - _slope / _intercept : coefficients pour tracer la droite
    """
    results = []
    for ttype, grp in df_input.groupby("type_local"):
        grp = grp.dropna(subset=["valeur_fonciere", "surface_reelle_bati"]).copy()
        grp = grp[(grp["surface_reelle_bati"] > 10) & (grp["valeur_fonciere"] > 10_000)]

        if len(grp) < 2:
            for col in ["prix_predit", "ecart", "ecart_pct", "_slope", "_intercept"]:
                grp[col] = float("nan")
            results.append(grp)
            continue

        x, y  = grp["surface_reelle_bati"], grp["valeur_fonciere"]
        n     = len(x)
        denom = n * (x ** 2).sum() - x.sum() ** 2

        if denom == 0:
            slope, intercept = 0.0, float(y.mean())
        else:
            slope     = (n * (x * y).sum() - x.sum() * y.sum()) / denom
            intercept = (y.sum() - slope * x.sum()) / n

        grp["_slope"]      = slope
        grp["_intercept"]  = intercept
        grp["prix_predit"] = (slope * x + intercept).round(0)
        grp["ecart"]       = (y - grp["prix_predit"]).round(0)
        grp["ecart_pct"]   = (grp["ecart"] / grp["prix_predit"] * 100).round(1)
        results.append(grp)

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


def compute_dvf_scores(
    df_input: pd.DataFrame,
    models: dict | None = None,
) -> pd.DataFrame:
    """
    Applique les coefficients DVF (calculés dynamiquement ou fallback config)
    à chaque annonce pour évaluer son écart vs le marché historique.

    Paramètres
    ----------
    df_input : DataFrame des annonces (doit contenir type_local,
               surface_reelle_bati, valeur_fonciere).
    models   : dict {"Appartement": {"slope": …, "intercept": …}, …}
               Si None, utilise DVF_REGRESSION (valeurs de repli de config.py).

    Colonnes ajoutées
    -----------------
      dvf_prix_predit  : prix attendu selon le modèle DVF
      dvf_ecart        : prix réel − dvf_prix_predit  (négatif = bonne affaire)
      dvf_ecart_pct    : écart en %
      _dvf_slope / _dvf_intercept : coefficients utilisés (pour tracer la droite)
    """
    _models = models if models is not None else DVF_REGRESSION

    df = df_input.copy()
    for col in ["dvf_prix_predit", "dvf_ecart", "dvf_ecart_pct", "_dvf_slope", "_dvf_intercept"]:
        df[col] = float("nan")

    for ttype, coef in _models.items():
        mask = (
            df["type_local"].eq(ttype)
            & df["surface_reelle_bati"].notna()
            & df["valeur_fonciere"].notna()
            & (df["surface_reelle_bati"] > 10)
            & (df["valeur_fonciere"] > 10_000)
        )
        if not mask.any():
            continue
        x = df.loc[mask, "surface_reelle_bati"]
        y = df.loc[mask, "valeur_fonciere"]
        predicted = (coef["slope"] * x + coef["intercept"]).round(0)
        df.loc[mask, "_dvf_slope"]      = coef["slope"]
        df.loc[mask, "_dvf_intercept"]  = coef["intercept"]
        df.loc[mask, "dvf_prix_predit"] = predicted
        df.loc[mask, "dvf_ecart"]       = (y - predicted).round(0)
        df.loc[mask, "dvf_ecart_pct"]   = ((y - predicted) / predicted * 100).round(1)

    return df
