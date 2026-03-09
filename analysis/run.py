import pandas as pd
from analysis.stats import mean, correlation
from analysis.regression import least_squares_fit

# 1. Charger les données (Pandas est autorisé pour la lecture, pas pour les calculs)
df = pd.read_csv("donnees/dvf_toulon.csv")

# 2. NETTOYAGE si besoin 


# On repasse en listes Python pour les calculs statistiques
prix = df['valeur_fonciere'].tolist()
surfaces = df['surface_reelle_bati'].tolist()

