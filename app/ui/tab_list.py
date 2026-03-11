"""Onglet 2 — Liste des biens avec tableau + fiches détaillées."""

import pandas as pd
import streamlit as st

from ui.components import market_badge_html, tags_html


def render_list(df: pd.DataFrame) -> None:
    st.markdown(f"**{len(df):,} bien(s)** correspondent à vos critères")

    if df.empty:
        st.info("😕 Aucune annonce ne correspond à vos filtres.")
        return

    # ── Tableau ──────────────────────────────────────────────────────────────
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
    df_disp = (
        df[[c for c in COLS if c in df.columns]]
        .copy()
        .rename(columns=COLS)
        .sort_values("Prix (€)", ascending=True)
    )
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
        ep_lst  = row.get("ecart_pct")
        tags    = row.get("tags", [])
        source  = str(row.get("source", "")).upper()

        lbl = titre
        if pd.notna(prix):    lbl += f"  ·  {prix:,.0f} €"
        if pd.notna(surface): lbl += f"  ·  {surface:.0f} m²"
        if pd.notna(ep_lst):
            ep_f = float(ep_lst)
            if ep_f < -10:  lbl += "  🎯"
            elif ep_f < -5: lbl += "  ✅"
            elif ep_f > 10: lbl += "  ⚠️"

        with st.expander(lbl):
            left, right = st.columns([1, 2], gap="medium")

            with left:
                if pd.notna(ep_lst):
                    st.markdown(market_badge_html(float(ep_lst)), unsafe_allow_html=True)
                    prix_p  = row.get("prix_predit")
                    ecart_e = row.get("ecart")
                    if pd.notna(prix_p) and pd.notna(ecart_e):
                        st.caption(f"Prix attendu : {prix_p:,.0f} €  ·  Écart : {ecart_e:+,.0f} €")

                if pd.notna(prix):
                    st.markdown(
                        f'<span class="prix-badge">{prix:,.0f} €</span>'
                        + (f' <span class="pm2-badge">{pm2:,.0f} €/m²</span>' if pd.notna(pm2) else ""),
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
                    st.markdown(f"[🔗 Voir l'annonce →]({url})")

            with right:
                if tags:
                    st.markdown(tags_html(tags), unsafe_allow_html=True)
                desc = str(row.get("description", "")).strip()
                if desc and desc != "nan":
                    st.markdown(
                        f"<small style='color:#475569;line-height:1.6'>"
                        f"{desc[:700]}{'…' if len(desc) > 700 else ''}</small>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Pas de description disponible.")
