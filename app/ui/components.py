"""
Composants HTML réutilisables et helpers NLP.
Pas de dépendance Streamlit — utilisable dans tests unitaires.
"""

from config import NLP_TAGS


def extract_tags(description: str) -> list[tuple[str, str]]:
    """Extrait les tags NLP depuis une description d'annonce."""
    if not isinstance(description, str):
        return []
    d = description.lower()
    return [(lbl, css) for lbl, (kws, css) in NLP_TAGS.items() if any(k in d for k in kws)]


def tags_html(tags: list[tuple[str, str]]) -> str:
    """Génère le HTML pour afficher les tags NLP."""
    return "".join(f'<span class="tag {css}">{lbl}</span>' for lbl, css in tags)


def market_badge_html(ecart_pct: float) -> str:
    """Badge HTML coloré selon la classification marché (4 niveaux)."""
    if ecart_pct < -10:
        return f'<span class="badge-opport">🎯 OPPORTUNITÉ &nbsp;{ecart_pct:.0f}%</span>'
    elif ecart_pct < -5:
        return f'<span class="badge-bonne">✅ Bonne affaire &nbsp;{ecart_pct:.0f}%</span>'
    elif ecart_pct <= 5:
        return f'<span class="badge-normal">✅ Prix normal &nbsp;{ecart_pct:+.0f}%</span>'
    else:
        return f'<span class="badge-eleve">⚠️ Prix élevé &nbsp;{ecart_pct:+.0f}%</span>'
