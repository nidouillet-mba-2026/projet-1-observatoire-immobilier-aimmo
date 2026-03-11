"""Onglet 1 — Analyse de marché (graphiques)."""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_analysis(df: pd.DataFrame) -> None:
    col_l, col_r = st.columns(2, gap="medium")

    # ── 1. Types de biens (Pie) ──────────────────────────────────────────────
    with col_l:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 🏠 Types de biens")
        if not df.empty:
            typ = df["type_local"].value_counts().reset_index()
            typ.columns = ["Type", "Annonces"]
            fig = px.pie(
                typ, names="Type", values="Annonces",
                color="Type",
                color_discrete_map={"Appartement": "#E8714A", "Maison": "#1B2B4B"},
                hole=0.5,
            )
            fig.update_layout(
                height=280, margin=dict(t=10, b=10, l=0, r=0),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="white",
            )
            fig.update_traces(textinfo="percent+label", textfont_size=13)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 2. Distribution des prix (Histogramme) ───────────────────────────────
    with col_r:
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
                height=280, margin=dict(t=10, b=10, l=0, r=0),
                paper_bgcolor="white", plot_bgcolor="white",
                bargap=0.1, legend_title_text="",
                legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            )
            fig.update_xaxes(tickformat=",.0f", ticksuffix=" €")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas assez de données.")
        st.markdown('</div>', unsafe_allow_html=True)

    col_l2, col_r2 = st.columns(2, gap="medium")

    # ── 3. Prix vs Surface (Scatter) ─────────────────────────────────────────
    with col_l2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 🔵 Prix en fonction de la surface")
        df_sc = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])
        if not df_sc.empty:
            size_vals = df_sc["prix_m2"].fillna(0).astype(float).tolist()
            fig = px.scatter(
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
            fig.update_layout(
                height=300, margin=dict(t=10, b=10, l=0, r=0),
                paper_bgcolor="white", plot_bgcolor="white",
                legend_title_text="",
                legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            )
            fig.update_yaxes(tickformat=",.0f", ticksuffix=" €")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas assez de données.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 4. Répartition par Sources (Bar) ──────────────────────────────────────
    with col_r2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 📡 Répartition par Sources")
        if not df.empty:
            src = df["source"].value_counts().reset_index()
            src.columns = ["Source", "Annonces"]
            fig = px.bar(
                src, x="Source", y="Annonces",
                color="Source",
                color_discrete_sequence=["#E8714A", "#1B2B4B", "#27AE60", "#8B5CF6"],
                template="simple_white", text="Annonces",
            )
            fig.update_traces(textposition="outside", marker_line_width=0)
            fig.update_layout(
                height=300, margin=dict(t=20, b=10, l=0, r=0),
                showlegend=False, paper_bgcolor="white", plot_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
