"""
Observatoire Immobilier AIMMO — Toulon ≤ 500 000 €
Dashboard SaaS — Marché immobilier toulonnais en temps réel
"""

import re
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ── Config page ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AIMMO — Observatoire Immobilier Toulon",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Personnalisé ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F0F2F6; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #1B2B4B; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: #E8714A !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stNumberInput label { color: #AABBCC !important; }

    /* Header */
    .aimmo-header {
        background: linear-gradient(135deg, #1B2B4B 0%, #2C3E6B 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(27,43,75,0.3);
    }
    .aimmo-header h1 { color: white; margin: 0; font-size: 28px; font-weight: 700; }
    .aimmo-header p  { color: #AABBCC; margin: 6px 0 0; font-size: 13px; }

    /* Métriques */
    div[data-testid="metric-container"] {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border-left: 4px solid #E8714A;
    }

    /* Tags NLP */
    .tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin: 2px;
    }
    .tag-blue   { background: #EBF5FB; color: #2980B9; }
    .tag-green  { background: #EAFAF1; color: #27AE60; }
    .tag-orange { background: #FEF9E7; color: #E67E22; }
    .tag-red    { background: #FDEDEC; color: #E74C3C; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/Karmadibsa/AImmo/"
    "feat/axel-verification/data/annonces.csv"
)
CSV_PATH = Path(__file__).parent.parent / "data" / "annonces.csv"

NLP_TAGS = {
    "Vue mer":      (["vue mer", "vue sur la mer", "panoramique mer"],   "tag-blue"),
    "Terrasse":     (["terrasse"],                                        "tag-green"),
    "Balcon":       (["balcon"],                                          "tag-green"),
    "Parking":      (["parking", "stationnement", "place de parking"],   "tag-orange"),
    "Garage":       (["garage", "box fermé", "box"],                     "tag-orange"),
    "Ascenseur":    (["ascenseur"],                                       "tag-blue"),
    "Rénové":       (["refait", "rénové", "rénovation", "neuf", "neuve"],"tag-green"),
    "Cave":         (["cave"],                                            "tag-orange"),
    "Piscine":      (["piscine"],                                         "tag-blue"),
    "Proche mer":   (["bord de mer", "pieds dans l'eau", "plages",
                      "proche mer", "400 mètres"],                       "tag-blue"),
}


def extract_tags(description: str) -> list:
    if not isinstance(description, str):
        return []
    desc_lower = description.lower()
    return [
        (label, css)
        for label, (keywords, css) in NLP_TAGS.items()
        if any(kw in desc_lower for kw in keywords)
    ]


def tags_html(tags: list) -> str:
    return " ".join(
        f'<span class="tag {css}">{label}</span>' for label, css in tags
    )


# ── Chargement données ─────────────────────────────────────────────────────────
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

    for col in ["latitude", "longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    mask = df["surface_reelle_bati"].fillna(0) > 0
    df["prix_m2"] = None
    df.loc[mask, "prix_m2"] = (
        df.loc[mask, "valeur_fonciere"] / df.loc[mask, "surface_reelle_bati"]
    ).round(0)

    if "date_mutation" in df.columns:
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")

    if "description" in df.columns:
        df["tags"] = df["description"].apply(extract_tags)

    return df


df_raw = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🏠 AIMMO")
    st.markdown("### Observatoire Immobilier")
    st.markdown("*Marché toulonnais — temps réel*")
    st.markdown("---")
    st.markdown("### 🎯 Filtres")

    types_dispo = sorted(df_raw["type_local"].dropna().unique().tolist()) if not df_raw.empty else []
    type_filtre = st.selectbox("Type de bien", ["Tous"] + types_dispo)

    budget_max = st.slider(
        "Budget maximum (€)",
        min_value=50_000, max_value=500_000, value=500_000,
        step=10_000, format="%d €",
    )

    surface_min = st.number_input("Surface minimum (m²)", min_value=0, max_value=300, value=0, step=5)
    pieces_min  = st.number_input("Pièces minimum",        min_value=0, max_value=8,   value=0, step=1)

    sources_dispo = sorted(df_raw["source"].dropna().unique().tolist()) if not df_raw.empty else []
    source_filtre = st.selectbox("Source", ["Toutes"] + sources_dispo)

    keyword = st.text_input("🔍 Mot-clé", placeholder="parking, terrasse, vue mer...")

    st.markdown("---")
    if not df_raw.empty and "date_mutation" in df_raw.columns:
        last_upd = df_raw["date_mutation"].max()
        if pd.notna(last_upd):
            st.markdown(f"🕐 **Dernière mise à jour**  \n`{last_upd.strftime('%d/%m/%Y %H:%M')}`")
        else:
            st.markdown("🕐 Date inconnue")
    st.markdown(f"📦 **{len(df_raw):,}** annonces en base")
    st.markdown("---")
    if st.button("🔄 Recharger les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ── Guard ──────────────────────────────────────────────────────────────────────
if df_raw.empty:
    st.markdown("""
    <div class="aimmo-header">
        <h1>🏠 Observatoire Immobilier — Toulon</h1>
        <p>PAP · SeLoger · LeBoncoin — Budget ≤ 500 000 €</p>
    </div>""", unsafe_allow_html=True)
    st.error("⚠️ Aucune donnée disponible.")
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
        df["description"].fillna("").str.contains(keyword, case=False, na=False) |
        df["titre"].fillna("").str.contains(keyword, case=False, na=False)
    )
    df = df[mask_kw]


# ── Header ─────────────────────────────────────────────────────────────────────
last_upd_str = ""
if not df_raw.empty and "date_mutation" in df_raw.columns:
    last_upd = df_raw["date_mutation"].max()
    if pd.notna(last_upd):
        last_upd_str = last_upd.strftime('%d/%m/%Y %H:%M')

st.markdown(f"""
<div class="aimmo-header">
    <h1>🏠 Observatoire Immobilier — Toulon</h1>
    <p>PAP · SeLoger · LeBoncoin — Budget ≤ 500 000 € · Dernière mise à jour : {last_upd_str or "inconnue"}</p>
</div>
""", unsafe_allow_html=True)


# ── KPI Row ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

nb_total   = len(df)
nb_delta   = len(df) - len(df_raw)
prix_med   = df["valeur_fonciere"].median()       if not df.empty and df["valeur_fonciere"].notna().any()       else None
surf_med   = df["surface_reelle_bati"].median()   if not df.empty and df["surface_reelle_bati"].notna().any() else None
pm2_med    = df["prix_m2"].median()               if not df.empty and df["prix_m2"].notna().any()            else None

c1.metric("📋 Annonces", f"{nb_total:,}",
          delta=f"{nb_delta:+,}" if nb_delta != 0 else None)
c2.metric("💰 Prix médian",
          f"{prix_med:,.0f} €" if prix_med else "—")
c3.metric("📐 Surface médiane",
          f"{surf_med:.0f} m²" if surf_med else "—")
c4.metric("💶 Prix médian /m²",
          f"{pm2_med:,.0f} €/m²" if pm2_med else "—")

st.markdown("<br>", unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_carte, tab_analyse, tab_liste = st.tabs([
    "🗺️  Carte interactive",
    "📊  Analyse de marché",
    "📋  Liste des biens",
])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — CARTE
# ════════════════════════════════════════════════════════════════════════════════
with tab_carte:
    df_map = df.dropna(subset=["latitude", "longitude"])
    df_map = df_map[(df_map["latitude"] != 0) & (df_map["longitude"] != 0)]

    if df_map.empty:
        st.info(
            "📍 **Aucune coordonnée GPS disponible pour les annonces actuelles.**\n\n"
            "La carte s'affichera automatiquement dès que les annonces incluront des coordonnées."
        )
    else:
        fig_map = px.scatter_mapbox(
            df_map,
            lat="latitude", lon="longitude",
            size="valeur_fonciere",
            color="prix_m2",
            hover_name="titre",
            hover_data={
                "valeur_fonciere":          ":,.0f",
                "surface_reelle_bati":      ":.0f",
                "prix_m2":                  ":.0f",
                "source":                   True,
                "latitude":                 False,
                "longitude":                False,
            },
            color_continuous_scale="RdYlGn_r",
            size_max=25,
            zoom=12,
            center={"lat": 43.125, "lon": 5.930},
            mapbox_style="carto-positron",
            labels={
                "valeur_fonciere":     "Prix (€)",
                "prix_m2":             "€/m²",
                "surface_reelle_bati": "Surface (m²)",
            },
        )
        fig_map.update_layout(height=560, margin=dict(t=0, b=0))
        st.plotly_chart(fig_map, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALYSE
# ════════════════════════════════════════════════════════════════════════════════
with tab_analyse:
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 📊 Distribution des prix")
        df_hist = df.dropna(subset=["valeur_fonciere"])
        if not df_hist.empty:
            fig = px.histogram(
                df_hist, x="valeur_fonciere", nbins=30, color="type_local",
                color_discrete_map={"Appartement": "#E8714A", "Maison": "#1B2B4B"},
                labels={"valeur_fonciere": "Prix (€)", "type_local": "Type", "count": "Nb"},
                template="simple_white",
            )
            fig.update_layout(bargap=0.08, height=320, margin=dict(t=10, b=10),
                              paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas assez de données.")

    with col_r:
        st.markdown("#### 🔵 Prix vs Surface")
        df_sc = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])
        if not df_sc.empty:
            fig2 = px.scatter(
                df_sc, x="surface_reelle_bati", y="valeur_fonciere", color="type_local",
                color_discrete_map={"Appartement": "#E8714A", "Maison": "#1B2B4B"},
                hover_data={
                    "nom_commune": True, "nombre_pieces_principales": True,
                    "source": True, "prix_m2": ":.0f",
                },
                labels={
                    "surface_reelle_bati": "Surface (m²)",
                    "valeur_fonciere": "Prix (€)",
                    "type_local": "Type",
                    "prix_m2": "€/m²",
                },
                template="simple_white", opacity=0.75,
            )
            fig2.update_layout(height=320, margin=dict(t=10, b=10),
                               paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Pas assez de données.")

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown("#### 📡 Répartition par source")
        if not df.empty and "source" in df.columns:
            src = df["source"].value_counts().reset_index()
            src.columns = ["Source", "Annonces"]
            fig3 = px.bar(
                src, x="Source", y="Annonces", color="Source",
                color_discrete_sequence=["#E8714A", "#1B2B4B", "#27AE60"],
                template="simple_white", text="Annonces",
            )
            fig3.update_traces(textposition="outside")
            fig3.update_layout(height=280, margin=dict(t=10, b=10), showlegend=False,
                               paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        st.markdown("#### 🏠 Répartition par type")
        if not df.empty and "type_local" in df.columns:
            typ = df["type_local"].value_counts().reset_index()
            typ.columns = ["Type", "Annonces"]
            fig4 = px.pie(
                typ, names="Type", values="Annonces",
                color="Type",
                color_discrete_map={"Appartement": "#E8714A", "Maison": "#1B2B4B"},
                template="simple_white",
            )
            fig4.update_layout(height=280, margin=dict(t=10, b=10))
            st.plotly_chart(fig4, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — LISTE
# ════════════════════════════════════════════════════════════════════════════════
with tab_liste:
    st.markdown(f"**{len(df):,} bien(s)** correspondant à vos critères")

    if df.empty:
        st.info("Aucune annonce ne correspond à vos filtres.")
    else:
        # ── Tableau avec column_config ─────────────────────────────────────────
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
        df_display = df[[c for c in COLS if c in df.columns]].copy()
        df_display = df_display.rename(columns=COLS)
        df_display = df_display.sort_values("Prix (€)", ascending=True)

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Lien":       st.column_config.LinkColumn("Lien", display_text="🔗 Voir"),
                "Titre":      st.column_config.TextColumn("Titre", width="large"),
                "Prix (€)":   st.column_config.NumberColumn("Prix (€)",    format="%.0f €"),
                "Surface (m²)": st.column_config.NumberColumn("Surface (m²)", format="%.0f m²"),
                "€/m²":       st.column_config.NumberColumn("€/m²",        format="%.0f €"),
                "Pièces":     st.column_config.NumberColumn("Pièces",       format="%d"),
            },
            height=380,
        )

        st.markdown("---")
        st.markdown("#### 🔍 Fiches détaillées")

        for _, row in df.iterrows():
            titre   = row.get("titre", "Annonce sans titre")
            prix    = row.get("valeur_fonciere")
            surface = row.get("surface_reelle_bati")
            pm2     = row.get("prix_m2")
            tags    = row.get("tags", [])

            label = str(titre)
            if pd.notna(prix):    label += f"  —  {prix:,.0f} €"
            if pd.notna(surface): label += f"  ·  {surface:.0f} m²"

            with st.expander(label):
                c_info, c_desc = st.columns([1, 2])

                with c_info:
                    st.markdown(f"**Source :** {row.get('source', '—')}")
                    st.markdown(f"**Type :** {row.get('type_local', '—')}")
                    if pd.notna(prix):    st.markdown(f"**Prix :** {prix:,.0f} €")
                    if pd.notna(surface): st.markdown(f"**Surface :** {surface:.0f} m²")
                    if pd.notna(pm2):     st.markdown(f"**Prix/m² :** {pm2:,.0f} €/m²")
                    pieces = row.get("nombre_pieces_principales")
                    if pd.notna(pieces):  st.markdown(f"**Pièces :** {int(pieces)}")
                    st.markdown(f"**Commune :** {row.get('nom_commune', '—')}")
                    url = row.get("url")
                    if pd.notna(url) and url:
                        st.markdown(f"[🔗 Voir l'annonce]({url})")

                with c_desc:
                    if tags:
                        st.markdown(tags_html(tags), unsafe_allow_html=True)
                        st.markdown("")
                    desc = row.get("description", "")
                    if pd.notna(desc) and str(desc).strip():
                        st.markdown(f"*{str(desc)[:600]}{'...' if len(str(desc)) > 600 else ''}*")
                    else:
                        st.markdown("*Pas de description disponible.*")
