"""
Constantes globales de l'application NidDouillet by AImmo.
Toutes les valeurs statiques (URLs, chemins, dictionnaires) sont ici.
"""

from pathlib import Path

# ── URLs & Chemins ──────────────────────────────────────────────────────────────
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/Karmadibsa/AImmo/"
    "feat/axel-verification/data/annonces.csv"
)
CSV_PATH = Path(__file__).parent.parent / "data" / "annonces.csv"

# ── Tags NLP (extraction depuis description) ────────────────────────────────────
NLP_TAGS: dict[str, tuple[list[str], str]] = {
    "Vue mer":    (["vue mer", "vue sur la mer", "vue panoramique"],    "tag-sea"),
    "Terrasse":   (["terrasse"],                                        "tag-green"),
    "Balcon":     (["balcon"],                                          "tag-green"),
    "Parking":    (["parking", "stationnement", "place de parking"],    "tag-orange"),
    "Garage":     (["garage", "box"],                                   "tag-orange"),
    "Ascenseur":  (["ascenseur"],                                       "tag-blue"),
    "Rénové":     (["refait", "rénové", "rénovation", "neuf", "neuve"], "tag-green"),
    "Cave":       (["cave"],                                            "tag-orange"),
    "Piscine":    (["piscine"],                                         "tag-blue"),
    "Proche mer": (["bord de mer", "pieds dans l'eau", "plages",
                    "proche mer", "400 mètres"],                        "tag-sea"),
}

# ── Coefficients DVF pré-calculés ───────────────────────────────────────────────
# Source : data/dvf_toulon.csv — ventes 2023-2025 (nature_mutation = Vente)
# Filtre : surface > 10 m², prix 10 000–500 000 €, Toulon uniquement
# Appartement : n=3 725, R²=0.141  |  Maison : n=393, R²=0.139
DVF_REGRESSION: dict[str, dict] = {
    "Appartement": {"slope": 1_661.0, "intercept":  76_761.0, "r2": 0.141, "n": 3_725},
    "Maison":      {"slope": 1_685.0, "intercept": 200_407.0, "r2": 0.139, "n":   393},
}
