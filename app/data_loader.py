"""
Chargement et pré-traitement des données immobilières.
Cache Streamlit (TTL 5 min) pour éviter les rechargements fréquents.
"""

import pandas as pd
import streamlit as st

from config import GITHUB_RAW_URL, CSV_PATH, DVF_CSV_PATH, DVF_REGRESSION, DVF_PM2_FILTERS
from analysis.regression import least_squares_fit, r_squared
from ui.components import extract_tags


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """
    Charge les données depuis GitHub (priorité) ou le CSV local (fallback).
    Retourne un DataFrame vide si aucune source n'est disponible.
    """
    try:
        df = pd.read_csv(GITHUB_RAW_URL, encoding="utf-8-sig")
    except Exception:
        if not CSV_PATH.exists():
            return pd.DataFrame()
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # Conversion numérique
    for col in ["valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Prix au m²
    mask = df["surface_reelle_bati"].fillna(0) > 0
    df["prix_m2"] = float("nan")
    df.loc[mask, "prix_m2"] = (
        df.loc[mask, "valeur_fonciere"] / df.loc[mask, "surface_reelle_bati"]
    ).round(0)
    df["prix_m2"] = pd.to_numeric(df["prix_m2"], errors="coerce")

    # Date
    if "date_mutation" in df.columns:
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")

    # Tags NLP
    if "description" in df.columns:
        df["tags"] = df["description"].apply(extract_tags)

    return df


@st.cache_data(ttl=300)
def get_dvf_models(dvf_csv_path: str = str(DVF_CSV_PATH)) -> dict:
    """
    Calcule dynamiquement les modèles OLS depuis dvf_toulon.csv.

    Applique les filtres prix/m² définis dans DVF_PM2_FILTERS pour éliminer
    les outliers et obtenir un R² cohérent avec les analyses locales (~0.67).

    Retourne un dict au format :
        {"Appartement": {"slope": …, "intercept": …, "r2": …, "n": …}, …}

    En cas d'erreur (fichier absent, trop peu de données), retourne DVF_REGRESSION
    (valeurs de repli définies dans config.py).
    """
    try:
        df = pd.read_csv(dvf_csv_path)

        # Nettoyage minimal
        for col in ("valeur_fonciere", "surface_reelle_bati"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

        models: dict = {}
        for ttype, (lo, hi) in DVF_PM2_FILTERS.items():
            sub = df[
                (df["type_local"] == ttype)
                & (df["nature_mutation"] == "Vente")
                & (df["surface_reelle_bati"] > 10)
                & (df["prix_m2"] >= lo)
                & (df["prix_m2"] <= hi)
            ].dropna(subset=["surface_reelle_bati", "valeur_fonciere"])

            if len(sub) < 10:
                # Pas assez de données → repli sur la valeur statique
                models[ttype] = DVF_REGRESSION.get(ttype, {})
                continue

            x = sub["surface_reelle_bati"].to_numpy(dtype=float)
            y = sub["valeur_fonciere"].to_numpy(dtype=float)
            slope, intercept = least_squares_fit(x, y)
            r2 = r_squared(x, y, slope, intercept)

            models[ttype] = {
                "slope":     round(slope, 1),
                "intercept": round(intercept, 1),
                "r2":        round(r2, 3),
                "n":         len(sub),
            }

        return models

    except Exception:
        return DVF_REGRESSION
