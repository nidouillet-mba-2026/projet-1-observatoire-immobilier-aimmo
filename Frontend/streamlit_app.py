"""
Observatoire Immobilier AIMMO — Toulon ≤ 500 000 €
Dashboard professionnel — Marché immobilier toulonnais en temps réel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Config page ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AIMMO — Observatoire Immobilier Toulon",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ─── Fond général ─── */
.stApp { background: #F4F6FA; }

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: #1B2B4B !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] small {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #E8714A !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #CBD5E1 !important;
}
/* Inputs sidebar */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #253859 !important;
    color: white !important;
    border-color: #3A5278 !important;
}
[data-testid="stSidebar"] .stSlider [data-testid="stTickBar"] {
    color: #CBD5E1 !important;
}

/* ─── Header ─── */
.aimmo-header {
    background: linear-gradient(135deg, #1B2B4B 0%, #2C4A8A 100%);
    padding: 28px 32px;
    border-radius: 16px;
    margin-bottom: 28px;
    box-shadow: 0 6px 24px rgba(27,43,75,0.25);
}
.aimmo-header h1 {
    color: white;
    margin: 0 0 6px 0;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.3px;
}
.aimmo-header .subtitle {
    color: #93B4D4;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}
.aimmo-header .badge {
    background: rgba(255,255,255,0.12);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    color: #BDD4EC;
}

/* ─── Métriques ─── */
[data-testid="metric-container"] {
    background: white;
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border-top: 3px solid #E8714A;
}
[data-testid="stMetricLabel"]  { color: #64748B !important; font-size: 13px !important; }
[data-testid="stMetricValue"]  { color: #1B2B4B !important; font-weight: 700 !important; }

/* ─── Onglets ─── */
[data-baseweb="tab-list"] {
    gap: 4px;
    background: white;
    padding: 6px 8px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
[data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    color: #64748B !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: #1B2B4B !important;
    color: white !important;
}

/* ─── Tags NLP ─── */
.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px 2px 2px 0;
}
.tag-blue   { background: #DBEAFE; color: #1D4ED8; }
.tag-green  { background: #DCFCE7; color: #16A34A; }
.tag-orange { background: #FEF3C7; color: #D97706; }
.tag-sea    { background: #CFFAFE; color: #0E7490; }

/* ─── Section card ─── */
.section-card {
    background: white;
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 16px;
}

/* ─── Prix badge ─── */
.prix-badge {
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    color: #C2410C;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 15px;
}
.pm2-badge {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1D4ED8;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 6px;
}

hr { border: none; border-top: 1px solid #E2E8F0; margin: 16px 0; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/Karmadibsa/AImmo/"
    "feat/axel-verification/data/annonces.csv"
)
CSV_PATH = Path(__file__).parent.parent / "data" / "annonces.csv"

NLP_TAGS = {
    "Vue mer":    (["vue mer", "vue sur la mer", "vue panoramique"],    "tag-sea"),
    "Terrasse":   (["terrasse"],                                        "tag-green"),
    "Balcon":     (["balcon"],                                          "tag-green"),
    "Parking":    (["parking", "stationnement", "place de parking"],   "tag-orange"),
    "Garage":     (["garage", "box"],                                  "tag-orange"),
    "Ascenseur":  (["ascenseur"],                                       "tag-blue"),
    "Rénové":     (["refait", "rénové", "rénovation", "neuf", "neuve"],"tag-green"),
    "Cave":       (["cave"],                                            "tag-orange"),
    "Piscine":    (["piscine"],                                         "tag-blue"),
    "Proche mer": (["bord de mer", "pieds dans l'eau", "plages",
                    "proche mer", "400 mètres"],                        "tag-sea"),
}


def extract_tags(description: str) -> list:
    if not isinstance(description, str):
        return []
    d = description.lower()
    return [(lbl, css) for lbl, (kws, css) in NLP_TAGS.items() if any(k in d for k in kws)]


def tags_html(tags: list) -> str:
    return "".join(f'<span class="tag {css}">{lbl}</span>' for lbl, css in tags)


# ── Régression linéaire ─────────────────────────────────────────────────────────
def compute_regression(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Régression linéaire prix ~ surface par type de bien (pure pandas, sans numpy/scipy).
    Enrichit le DataFrame avec :
      - prix_predit : prix attendu selon la droite de régression
      - ecart       : prix réel − prix prédit (négatif = sous-évalué)
      - ecart_pct   : écart en % du prix prédit
      - _slope / _intercept : coefficients pour tracer la droite
    """
    results = []
    for ttype, grp in df_input.groupby("type_local"):
        grp = grp.dropna(subset=["valeur_fonciere", "surface_reelle_bati"]).copy()
        # Filtre les cas aberrants
        grp = grp[(grp["surface_reelle_bati"] > 10) & (grp["valeur_fonciere"] > 10_000)]
        if len(grp) < 5:
            for col in ["prix_predit", "ecart", "ecart_pct", "_slope", "_intercept"]:
                grp[col] = float("nan")
            results.append(grp)
            continue

        x, y  = grp["surface_reelle_bati"], grp["valeur_fonciere"]
        n      = len(x)
        denom  = n * (x ** 2).sum() - x.sum() ** 2

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

    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True)


# ── Données ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(GITHUB_RAW_URL, encoding="utf-8-sig")
    except Exception:
        if not CSV_PATH.exists():
            return pd.DataFrame()
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    for col in ["valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    mask = df["surface_reelle_bati"].fillna(0) > 0
    df["prix_m2"] = float("nan")
    df.loc[mask, "prix_m2"] = (
        df.loc[mask, "valeur_fonciere"] / df.loc[mask, "surface_reelle_bati"]
    ).round(0)
    df["prix_m2"] = pd.to_numeric(df["prix_m2"], errors="coerce")

    if "date_mutation" in df.columns:
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")

    if "description" in df.columns:
        df["tags"] = df["description"].apply(extract_tags)

    return df


df_raw = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏠 AIMMO")
    st.markdown("**Observatoire Immobilier**")
    st.caption("Marché toulonnais — temps réel")
    st.markdown("---")

    st.markdown("### 🎯 Filtres")

    types_dispo = sorted(df_raw["type_local"].dropna().unique()) if not df_raw.empty else []
    type_filtre = st.selectbox("Type de bien", ["Tous"] + list(types_dispo))

    budget_max = st.slider("Budget max (€)", 50_000, 500_000, 500_000, 10_000, format="%d €")
    surface_min = st.number_input("Surface min (m²)", 0, 300, 0, 5)
    pieces_min  = st.number_input("Pièces min",        0, 8,   0, 1)

    sources_dispo = sorted(df_raw["source"].dropna().unique()) if not df_raw.empty else []
    source_filtre = st.selectbox("Source", ["Toutes"] + list(sources_dispo))

    keyword = st.text_input("🔍 Mot-clé", placeholder="terrasse, parking…")

    st.markdown("---")

    if not df_raw.empty and "date_mutation" in df_raw.columns:
        last_upd = df_raw["date_mutation"].max()
        st.caption("🕐 Dernière mise à jour")
        if pd.notna(last_upd):
            st.markdown(f"**`{last_upd.strftime('%d/%m/%Y %H:%M')}`**")

    st.caption(f"📦 {len(df_raw):,} annonces en base")
    st.markdown("---")

    if st.button("🔄 Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Guard ──────────────────────────────────────────────────────────────────────
if df_raw.empty:
    st.error("⚠️ Aucune donnée disponible. Vérifiez que le scraping a bien tourné.")
    st.stop()

# ── Filtrage ───────────────────────────────────────────────────────────────────
df = df_raw.copy()
if type_filtre != "Tous":
    df = df[df["type_local"] == type_filtre]
if budget_max < 500_000:
    df = df[df["valeur_fonciere"] <= budget_max]
if surface_min > 0:
    df = df[df["surface_reelle_bati"] >= surface_min]
if pieces_min > 0:
    df = df[df["nombre_pieces_principales"] >= pieces_min]
if source_filtre != "Toutes":
    df = df[df["source"] == source_filtre]
if keyword:
    mask_kw = (
        df["description"].fillna("").str.contains(keyword, case=False) |
        df["titre"].fillna("").str.contains(keyword, case=False)
    )
    df = df[mask_kw]

# ── Régression (calculée une fois après filtrage) ────────────────────────────────
df_scored = compute_regression(df[df["type_local"].notna()].copy()) if not df.empty else pd.DataFrame()

# ── Header ─────────────────────────────────────────────────────────────────────
last_upd_str = "—"
if not df_raw.empty and "date_mutation" in df_raw.columns:
    lu = df_raw["date_mutation"].max()
    if pd.notna(lu):
        last_upd_str = lu.strftime("%d/%m/%Y à %H:%M")

st.markdown(f"""
<div class="aimmo-header">
  <h1>🏠 Observatoire Immobilier — Toulon</h1>
  <div class="subtitle">
    <span class="badge">≤ 500 000 €</span>
    <span class="badge">PAP · LeBoncoin</span>
    <span>🕐 Mis à jour le {last_upd_str}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

prix_med  = df["valeur_fonciere"].median() if not df.empty and df["valeur_fonciere"].notna().any() else None
surf_med  = df["surface_reelle_bati"].median() if not df.empty and df["surface_reelle_bati"].notna().any() else None
pm2_med   = df["prix_m2"].median() if not df.empty and df["prix_m2"].notna().any() else None
delta_nb  = len(df) - len(df_raw) if len(df) != len(df_raw) else None

k1.metric("📋 Annonces", f"{len(df):,}", delta=f"{delta_nb:+}" if delta_nb else None)
k2.metric("💰 Prix médian",    f"{prix_med:,.0f} €"    if prix_med else "—")
k3.metric("📐 Surface médiane", f"{surf_med:.0f} m²"   if surf_med else "—")
k4.metric("💶 Prix/m² médian",  f"{pm2_med:,.0f} €/m²" if pm2_med else "—")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_analyse, tab_liste, tab_opps = st.tabs(["📊  Analyse de marché", "📋  Liste des biens", "💡  Opportunités"])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYSE
# ════════════════════════════════════════════════════════════════════════════════
with tab_analyse:

    col_l, col_r = st.columns(2, gap="medium")

    # Distribution des prix
    with col_l:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Distribution des prix")
        df_h = df.dropna(subset=["valeur_fonciere"])
        if not df_h.empty:
            fig = px.histogram(
                df_h, x="valeur_fonciere", nbins=20, color="type_local",
                color_discrete_map={"Appartement": "#E8714A", "Maison": "#1B2B4B"},
                labels={"valeur_fonciere": "Prix (€)", "type_local": "Type", "count": "Annonces"},
                template="simple_white",
            )
            fig.update_layout(
                height=300, margin=dict(t=10, b=10, l=0, r=0),
                paper_bgcolor="white", plot_bgcolor="white",
                bargap=0.1, legend_title_text="",
                legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            )
            fig.update_xaxes(tickformat=",.0f", ticksuffix=" €")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas assez de données.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Prix vs Surface
    with col_r:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 🔵 Prix en fonction de la surface")
        df_sc = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])
        if not df_sc.empty:
            # Convertir en liste Python pour éviter le bug narwhals/Plotly (Python 3.14)
            size_vals = df_sc["prix_m2"].fillna(0).astype(float).tolist()
            fig2 = px.scatter(
                df_sc, x="surface_reelle_bati", y="valeur_fonciere",
                color="type_local", size=size_vals,
                color_discrete_map={"Appartement": "#E8714A", "Maison": "#1B2B4B"},
                hover_name="titre",
                hover_data={"nombre_pieces_principales": True, "source": True,
                            "prix_m2": ":.0f", "surface_reelle_bati": False},
                labels={"surface_reelle_bati": "Surface (m²)", "valeur_fonciere": "Prix (€)",
                        "type_local": "Type", "prix_m2": "€/m²"},
                template="simple_white", opacity=0.8,
            )
            fig2.update_layout(
                height=300, margin=dict(t=10, b=10, l=0, r=0),
                paper_bgcolor="white", plot_bgcolor="white",
                legend_title_text="",
                legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            )
            fig2.update_yaxes(tickformat=",.0f", ticksuffix=" €")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Pas assez de données.")
        st.markdown('</div>', unsafe_allow_html=True)

    col_l2, col_r2 = st.columns(2, gap="medium")

    # Répartition source
    with col_l2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 📡 Sources")
        if not df.empty:
            src = df["source"].value_counts().reset_index()
            src.columns = ["Source", "Annonces"]
            fig3 = px.bar(
                src, x="Source", y="Annonces",
                color="Source",
                color_discrete_sequence=["#E8714A", "#1B2B4B", "#27AE60", "#8B5CF6"],
                template="simple_white", text="Annonces",
            )
            fig3.update_traces(textposition="outside", marker_line_width=0)
            fig3.update_layout(
                height=260, margin=dict(t=20, b=10, l=0, r=0),
                showlegend=False, paper_bgcolor="white", plot_bgcolor="white",
            )
            st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Répartition type
    with col_r2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 🏠 Types de biens")
        if not df.empty:
            typ = df["type_local"].value_counts().reset_index()
            typ.columns = ["Type", "Annonces"]
            fig4 = px.pie(
                typ, names="Type", values="Annonces",
                color="Type",
                color_discrete_map={"Appartement": "#E8714A", "Maison": "#1B2B4B"},
                hole=0.5,
            )
            fig4.update_layout(
                height=260, margin=dict(t=10, b=10, l=0, r=0),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            )
            fig4.update_traces(textinfo="percent+label", textfont_size=13)
            st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — LISTE
# ════════════════════════════════════════════════════════════════════════════════
with tab_liste:
    st.markdown(f"**{len(df):,} bien(s)** correspondent à vos critères")

    if df.empty:
        st.info("😕 Aucune annonce ne correspond à vos filtres.")
    else:
        # ── Tableau ────────────────────────────────────────────────────────────
        COLS = {
            "source":                    "Source",
            "type_local":                "Type",
            "titre":                     "Titre",
            "valeur_fonciere":           "Prix (€)",
            "surface_reelle_bati":       "Surface (m²)",
            "nombre_pieces_principales": "Pièces",
            "prix_m2":                   "€/m²",
            "nom_commune":               "Commune",
            "url":                       "Lien",
        }
        df_disp = df[[c for c in COLS if c in df.columns]].copy()
        df_disp = df_disp.rename(columns=COLS).sort_values("Prix (€)", ascending=True)

        st.dataframe(
            df_disp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Lien":         st.column_config.LinkColumn("Lien", display_text="🔗 Voir"),
                "Titre":        st.column_config.TextColumn("Titre", width="large"),
                "Prix (€)":     st.column_config.NumberColumn("Prix (€)",     format="%.0f €"),
                "Surface (m²)": st.column_config.NumberColumn("Surface (m²)", format="%.0f m²"),
                "€/m²":         st.column_config.NumberColumn("€/m²",         format="%.0f €"),
                "Pièces":       st.column_config.NumberColumn("Pièces",        format="%d"),
            },
            height=360,
        )

        st.markdown("---")
        st.markdown("#### 🔍 Fiches détaillées")

        for _, row in df.iterrows():
            titre   = str(row.get("titre", "Annonce sans titre"))
            prix    = row.get("valeur_fonciere")
            surface = row.get("surface_reelle_bati")
            pm2     = row.get("prix_m2")
            tags    = row.get("tags", [])
            source  = str(row.get("source", "")).upper()

            # Label expander
            lbl = titre
            if pd.notna(prix):    lbl += f"  ·  {prix:,.0f} €"
            if pd.notna(surface): lbl += f"  ·  {surface:.0f} m²"

            with st.expander(lbl):
                left, right = st.columns([1, 2], gap="medium")

                with left:
                    # Badges prix
                    if pd.notna(prix):
                        st.markdown(
                            f'<span class="prix-badge">{prix:,.0f} €</span>'
                            + (f' <span class="pm2-badge">{pm2:,.0f} €/m²</span>' if pd.notna(pm2) else ""),
                            unsafe_allow_html=True,
                        )
                        st.markdown("")

                    info_lines = [
                        ("🏷️ Source",   source),
                        ("🏠 Type",     row.get("type_local", "—")),
                        ("📐 Surface",  f"{surface:.0f} m²" if pd.notna(surface) else "—"),
                        ("🚪 Pièces",   f"{int(row['nombre_pieces_principales'])}" if pd.notna(row.get("nombre_pieces_principales")) else "—"),
                        ("📍 Commune",  row.get("nom_commune", "—")),
                    ]
                    for icon_lbl, val in info_lines:
                        st.markdown(f"**{icon_lbl}** : {val}")

                    url = row.get("url")
                    if pd.notna(url) and url:
                        st.markdown(f"<br>[🔗 Voir l'annonce →]({url})", unsafe_allow_html=True)

                with right:
                    if tags:
                        st.markdown(tags_html(tags), unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                    desc = str(row.get("description", "")).strip()
                    if desc and desc != "nan":
                        st.markdown(
                            f"<small style='color:#475569;line-height:1.6'>"
                            f"{desc[:700]}{'…' if len(desc) > 700 else ''}"
                            f"</small>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("Pas de description disponible.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — OPPORTUNITÉS (régression linéaire prix ~ surface)
# ════════════════════════════════════════════════════════════════════════════════
with tab_opps:

    if df_scored.empty or "ecart_pct" not in df_scored.columns:
        st.info("😕 Pas assez de données pour calculer la régression.")
    else:
        # ── Explication méthodo ────────────────────────────────────────────────
        st.markdown("""
        <div class="section-card" style="border-top-color:#27AE60;">
        <strong>🔬 Méthodologie</strong> — Pour chaque type de bien (Appartement / Maison),
        on calcule une droite de régression linéaire <em>Prix = a × Surface + b</em> à partir
        de toutes les annonces filtrées. L'<strong>écart</strong> = Prix réel − Prix prédit :
        un écart <span style="color:#16A34A;font-weight:600">négatif</span> signifie que le bien est
        <strong>moins cher que ce que le marché laisserait attendre</strong> pour sa surface
        — c'est une opportunité potentielle.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Opportunités = écart < -10 % ──────────────────────────────────────
        df_opps = df_scored[df_scored["ecart_pct"] < -10].sort_values("ecart_pct")
        n_opps  = len(df_opps)

        # Meilleures économies médianes
        econ_med = df_opps["ecart"].median() if n_opps > 0 else None
        best_row  = df_opps.iloc[0] if n_opps > 0 else None

        # ── KPIs ──────────────────────────────────────────────────────────────
        ko1, ko2, ko3 = st.columns(3)
        ko1.metric("🎯 Opportunités détectées",
                   f"{n_opps}",
                   delta=f"écart > 10 % sous le marché")
        if best_row is not None and pd.notna(best_row["ecart_pct"]):
            ko2.metric("🏆 Meilleure affaire",
                       f"{best_row['ecart_pct']:.1f} %",
                       delta=f"{best_row['ecart']:,.0f} € sous le marché")
        else:
            ko2.metric("🏆 Meilleure affaire", "—")
        ko3.metric("💰 Économie médiane",
                   f"{abs(econ_med):,.0f} €" if econ_med else "—",
                   delta="par rapport au prix attendu")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Scatter prix vs surface + droites de régression ─────────────────
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 📈 Prix vs Surface — avec droite de régression")

        COLORS_TYPE = {"Appartement": "#E8714A", "Maison": "#1B2B4B"}
        fig_reg = go.Figure()

        for ttype, grp in df_scored.groupby("type_local"):
            c = COLORS_TYPE.get(ttype, "#8B5CF6")
            grp_valid = grp.dropna(subset=["_slope", "_intercept",
                                            "surface_reelle_bati", "valeur_fonciere"])
            if grp_valid.empty:
                continue

            # Points — couleur selon sur/sous-évaluation
            fig_reg.add_trace(go.Scatter(
                x=grp_valid["surface_reelle_bati"].tolist(),
                y=grp_valid["valeur_fonciere"].tolist(),
                mode="markers",
                name=ttype,
                marker=dict(
                    color=grp_valid["ecart_pct"].tolist(),
                    colorscale="RdYlGn_r",
                    cmin=-30, cmax=30,
                    size=8,
                    opacity=0.75,
                    line=dict(width=0),
                    showscale=False,
                ),
                text=grp_valid["titre"].fillna("").tolist(),
                customdata=list(zip(
                    grp_valid["ecart_pct"].tolist(),
                    grp_valid["ecart"].fillna(0).tolist(),
                    grp_valid["prix_predit"].fillna(0).tolist(),
                )),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Surface : %{x:.0f} m²<br>"
                    "Prix réel : %{y:,.0f} €<br>"
                    "Prix attendu : %{customdata[2]:,.0f} €<br>"
                    "Écart : <b>%{customdata[0]:.1f} %</b> (%{customdata[1]:+,.0f} €)"
                    "<extra>" + ttype + "</extra>"
                ),
            ))

            # Droite de régression
            slope     = float(grp_valid["_slope"].iloc[0])
            intercept = float(grp_valid["_intercept"].iloc[0])
            x_min     = float(grp_valid["surface_reelle_bati"].min())
            x_max     = float(grp_valid["surface_reelle_bati"].max())
            fig_reg.add_trace(go.Scatter(
                x=[x_min, x_max],
                y=[slope * x_min + intercept, slope * x_max + intercept],
                mode="lines",
                name=f"Tendance {ttype}",
                line=dict(color=c, width=2, dash="dash"),
            ))

        # Colorbar légende
        fig_reg.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(
                colorscale="RdYlGn_r", cmin=-30, cmax=30,
                color=[0], showscale=True,
                colorbar=dict(
                    title="Écart (%)",
                    tickvals=[-30, -15, 0, 15, 30],
                    ticktext=["-30 %", "-15 %", "0 %", "+15 %", "+30 %"],
                    thickness=12, len=0.6,
                ),
            ),
            showlegend=False,
        ))

        fig_reg.update_layout(
            height=380, margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="white", plot_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            xaxis_title="Surface (m²)", yaxis_title="Prix (€)",
        )
        fig_reg.update_yaxes(tickformat=",.0f", ticksuffix=" €")
        st.plotly_chart(fig_reg, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Graphique top 15 + tableau ─────────────────────────────────────────
        col_bar, col_tbl = st.columns([1, 1], gap="large")

        with col_bar:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("#### 🏅 Top 15 meilleures affaires")
            top15 = df_opps.head(15).copy()
            if not top15.empty:
                top15["label"] = (
                    top15["titre"].fillna("Annonce").str[:35] + "…"
                )
                fig_bar = px.bar(
                    top15,
                    x="ecart_pct",
                    y="label",
                    orientation="h",
                    color="ecart_pct",
                    color_continuous_scale="RdYlGn_r",
                    range_color=[-40, 0],
                    text=top15["ecart_pct"].apply(lambda v: f"{v:.1f} %"),
                    labels={"ecart_pct": "Écart (%)", "label": ""},
                    template="simple_white",
                )
                fig_bar.update_traces(textposition="outside")
                fig_bar.update_layout(
                    height=420, margin=dict(t=10, b=10, l=0, r=10),
                    paper_bgcolor="white", plot_bgcolor="white",
                    showlegend=False, coloraxis_showscale=False,
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Aucune opportunité détectée avec les filtres actuels.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_tbl:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("#### 📋 Tableau des opportunités")
            if not df_opps.empty:
                COLS_OPP = {
                    "titre":               "Titre",
                    "type_local":          "Type",
                    "valeur_fonciere":     "Prix réel (€)",
                    "prix_predit":         "Prix attendu (€)",
                    "ecart":               "Économie (€)",
                    "ecart_pct":           "Écart (%)",
                    "surface_reelle_bati": "Surface (m²)",
                    "url":                 "Lien",
                }
                df_tbl = df_opps[[c for c in COLS_OPP if c in df_opps.columns]].copy()
                df_tbl = df_tbl.rename(columns=COLS_OPP)

                st.dataframe(
                    df_tbl,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Lien":           st.column_config.LinkColumn("Lien", display_text="🔗 Voir"),
                        "Titre":          st.column_config.TextColumn("Titre", width="medium"),
                        "Prix réel (€)":  st.column_config.NumberColumn(format="%.0f €"),
                        "Prix attendu (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Économie (€)":   st.column_config.NumberColumn(format="%.0f €"),
                        "Écart (%)":      st.column_config.NumberColumn(format="%.1f %%"),
                        "Surface (m²)":   st.column_config.NumberColumn(format="%.0f m²"),
                    },
                    height=420,
                )
            else:
                st.info("Aucune opportunité pour les filtres actuels.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Fiches des top opportunités ─────────────────────────────────────────
        if not df_opps.empty:
            st.markdown("---")
            st.markdown("#### 🔍 Fiches détaillées — Meilleures opportunités")
            for _, row in df_opps.head(20).iterrows():
                titre   = str(row.get("titre", "Annonce sans titre"))
                prix    = row.get("valeur_fonciere")
                surface = row.get("surface_reelle_bati")
                pm2     = row.get("prix_m2")
                ecart_p = row.get("ecart_pct")
                ecart_e = row.get("ecart")
                tags    = row.get("tags", [])
                source  = str(row.get("source", "")).upper()

                lbl = titre
                if pd.notna(prix):    lbl += f"  ·  {prix:,.0f} €"
                if pd.notna(surface): lbl += f"  ·  {surface:.0f} m²"
                if pd.notna(ecart_p): lbl += f"  ·  🟢 {ecart_p:.1f} %"

                with st.expander(lbl):
                    left, right = st.columns([1, 2], gap="medium")

                    with left:
                        if pd.notna(prix):
                            st.markdown(
                                f'<span class="prix-badge">{prix:,.0f} €</span>'
                                + (f' <span class="pm2-badge">{pm2:,.0f} €/m²</span>'
                                   if pd.notna(pm2) else ""),
                                unsafe_allow_html=True,
                            )
                            st.markdown("")

                        if pd.notna(ecart_p) and pd.notna(ecart_e):
                            savings_color = "#16A34A" if ecart_e < 0 else "#DC2626"
                            st.markdown(
                                f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;'
                                f'border-radius:8px;padding:8px 12px;margin:6px 0;">'
                                f'<span style="color:{savings_color};font-weight:700;font-size:14px;">'
                                f'{"📉" if ecart_e < 0 else "📈"} {ecart_p:+.1f} % vs marché</span><br>'
                                f'<span style="color:#475569;font-size:12px;">'
                                f'Soit {abs(ecart_e):,.0f} € {"en dessous" if ecart_e < 0 else "au dessus"} '
                                f'du prix attendu</span></div>',
                                unsafe_allow_html=True,
                            )

                        info_lines = [
                            ("🏷️ Source",  source),
                            ("🏠 Type",    row.get("type_local", "—")),
                            ("📐 Surface", f"{surface:.0f} m²" if pd.notna(surface) else "—"),
                            ("🚪 Pièces",  f"{int(row['nombre_pieces_principales'])}"
                             if pd.notna(row.get("nombre_pieces_principales")) else "—"),
                            ("📍 Commune", row.get("nom_commune", "—")),
                        ]
                        for icon_lbl, val in info_lines:
                            st.markdown(f"**{icon_lbl}** : {val}")

                        url = row.get("url")
                        if pd.notna(url) and url:
                            st.markdown(f"<br>[🔗 Voir l'annonce →]({url})", unsafe_allow_html=True)

                    with right:
                        if tags:
                            st.markdown(tags_html(tags), unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)

                        desc = str(row.get("description", "")).strip()
                        if desc and desc != "nan":
                            st.markdown(
                                f"<small style='color:#475569;line-height:1.6'>"
                                f"{desc[:700]}{'…' if len(desc) > 700 else ''}"
                                f"</small>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.caption("Pas de description disponible.")
