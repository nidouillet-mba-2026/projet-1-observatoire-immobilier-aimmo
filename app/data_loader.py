"""
Chargement et pré-traitement des données immobilières.
Cache Streamlit (TTL 5 min) pour éviter les rechargements fréquents.
"""

import pandas as pd
import streamlit as st

from config import GITHUB_RAW_URL, CSV_PATH
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
