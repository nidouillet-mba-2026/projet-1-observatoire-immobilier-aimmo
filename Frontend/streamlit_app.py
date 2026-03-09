"""
streamlit_app.py — NidBot Conversational Interface
Run: streamlit run streamlit_app.py
"""

import streamlit as st
import requests
import json
import base64
import os
from datetime import datetime

# ======================================================
# ================== CONFIG ===========================
# ======================================================

API_URL = os.getenv("API_URL", "http://localhost:8000")  # FastAPI backend

st.set_page_config(
    page_title="NidBot — NidDouillet",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================================================
# ================== STYLES ===========================
# ======================================================

st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F8F9FA; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #1B2B4B; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 { color: #E8714A !important; }

    /* Chat bubbles */
    .chat-user {
        background-color: #1B2B4B;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 6px 0;
        max-width: 75%;
        float: right;
        clear: both;
        font-size: 14px;
    }
    .chat-bot {
        background-color: white;
        color: #1B2B4B;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 6px 0;
        max-width: 80%;
        float: left;
        clear: both;
        font-size: 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 3px solid #E8714A;
    }
    .clearfix { clear: both; }

    /* Property cards */
    .property-card {
        background: white;
        border-radius: 12px;
        padding: 14px 16px;
        margin: 8px 0;
        border-left: 4px solid #E8714A;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    .property-card.undervalued { border-left-color: #27AE60; }
    .property-price {
        font-size: 18px;
        font-weight: bold;
        color: #E8714A;
    }
    .badge-undervalued {
        background-color: #27AE60;
        color: white;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
    }
    .score-bar-bg {
        background: #EEEEEE;
        border-radius: 4px;
        height: 6px;
        width: 100%;
        margin-top: 4px;
    }

    /* Input area */
    .stTextInput input, .stChatInput input {
        border-radius: 24px !important;
        border: 2px solid #1B2B4B !important;
    }

    /* Buttons */
    .stButton button {
        border-radius: 20px;
        background-color: #E8714A;
        color: white;
        border: none;
        font-weight: 600;
    }
    .stButton button:hover { background-color: #d4603a; }

    /* Header */
    .nid-header {
        background: linear-gradient(135deg, #1B2B4B 0%, #2C3E6B 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .nid-header h1 { color: white; margin: 0; font-size: 24px; }
    .nid-header p { color: #AABBCC; margin: 4px 0 0; font-size: 13px; }
</style>
""", unsafe_allow_html=True)


# ======================================================
# ================== SESSION STATE ====================
# ======================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_properties" not in st.session_state:
    st.session_state.last_properties = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = False
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "criteria" not in st.session_state:
    st.session_state.criteria = {}


# ======================================================
# ================== HELPERS ==========================
# ======================================================

def _generate_pdf():
    """Call backend to generate PDF and store path"""
    summary_parts = []
    for msg in st.session_state.messages[-4:]:
        if msg["role"] == "user":
            summary_parts.append(msg["content"])
    summary = " | ".join(summary_parts) or "Recherche immobilière à Toulon"

    try:
        resp = requests.post(
            f"{API_URL}/generate-pdf",
            json={
                "properties": st.session_state.last_properties,
                "conversation_summary": summary,
                "client_criteria": st.session_state.criteria
            },
            timeout=30
        )
        data = resp.json()
        if data.get("status") == "ok":
            st.session_state.pdf_path = data["path"]
            st.success("Rapport généré !")
        else:
            st.error(f"Erreur : {data.get('message')}")
    except Exception as e:
        st.error(f"Impossible de contacter l'API : {e}")


def send_message(prompt: str):
    """Send prompt to backend and store response"""
    st.session_state.messages.append({"role": "user", "content": prompt})

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    # Merge criteria into prompt if filters set
    enriched_prompt = prompt
    crit = st.session_state.criteria
    if crit.get("budget") and crit["budget"] < 450000:
        enriched_prompt += f" (budget max {crit['budget']:,}€)"
    if crit.get("surface_min"):
        enriched_prompt += f" (surface min {crit['surface_min']}m²)"
    if crit.get("rooms_min"):
        enriched_prompt += f" ({crit['rooms_min']} pièces minimum)"
    if crit.get("location") and crit["location"] != "toulon":
        enriched_prompt += f" à {crit['location']}"

    try:
        resp = requests.post(
            f"{API_URL}/chat",
            json={"prompt": enriched_prompt, "conversation_history": history},
            timeout=60
        )
        
        # Vérifier le statut HTTP
        if resp.status_code != 200:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Erreur serveur (HTTP {resp.status_code}): {resp.text[:200]}",
                "properties": []
            })
            st.rerun()
            return
        
        data = resp.json()
        bot_response = data.get("response", "Erreur de réponse.")
        properties = data.get("properties", [])

        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_response,
            "properties": properties
        })

        if properties:
            st.session_state.last_properties = properties

    except requests.exceptions.ConnectionError:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⚠️ Impossible de contacter le serveur NidBot.\n\nVérifiez que le backend FastAPI est lancé : `uvicorn main:app --reload`",
            "properties": []
        })
    except requests.exceptions.JSONDecodeError as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Erreur de réponse JSON: {str(e)}\n\nLa réponse du serveur n'est pas au format JSON attendu.",
            "properties": []
        })
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Erreur inattendue: {str(e)}",
            "properties": []
        })


def render_property_card(prop: dict, index: int):
    """Render a compact property card"""
    is_uv = prop.get("is_undervalued", False)
    score = prop.get("score", 0)
    market = prop.get("market_price_per_m2", 0)
    ecart = ((prop["price_per_m2"] / market) - 1) * 100 if market else 0

    card_class = "property-card undervalued" if is_uv else "property-card"
    badge = '<span class="badge-undervalued">✅ SOUS-ÉVALUÉ</span>' if is_uv else ""
    ecart_color = "#27AE60" if ecart < -5 else ("#E74C3C" if ecart > 5 else "#888")
    score_width = min(score, 100)

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <b style="color:#1B2B4B;">#{index} — {prop['type']}</b> {badge}<br>
                <span style="font-size:12px; color:#666;">📍 {prop['address']}, {prop['neighborhood'].title()}</span>
            </div>
            <div class="property-price">{prop['price']:,.0f} €</div>
        </div>
        <div style="margin-top:8px; display:flex; gap:16px; font-size:12px; color:#555;">
            <span>📐 {prop['surface']} m²</span>
            <span>🚪 {prop['rooms']} pièces</span>
            <span>💰 {prop['price_per_m2']:,.0f} €/m²</span>
            <span style="color:{ecart_color};">vs marché : {ecart:+.1f}%</span>
        </div>
        <div style="margin-top:6px;">
            <span style="font-size:11px; color:#888;">Score NidBot : {score}/100</span>
            <div class="score-bar-bg"><div style="background:#E8714A; height:6px; border-radius:4px; width:{score_width}%;"></div></div>
        </div>
        <div style="margin-top:5px; font-size:11px; color:#888;">{prop.get('description','')}</div>
        <div style="font-size:10px; color:#bbb; margin-top:2px;">Source : {prop.get('source','N/A')} | Réf : {prop.get('ref','N/A')}</div>
    </div>
    """, unsafe_allow_html=True)


# ======================================================
# ================== SIDEBAR ==========================
# ======================================================

with st.sidebar:
    st.markdown("# 🏠 NidDouillet")
    st.markdown("### NidBot — Conseiller IA")
    st.markdown("---")

    st.markdown("### 🎯 Filtres rapides")

    budget = st.slider(
        "Budget maximum (€)",
        min_value=100000,
        max_value=450000,
        value=450000,
        step=10000,
        format="%d €"
    )

    surface = st.number_input("Surface minimum (m²)", min_value=0, max_value=200, value=0, step=5)
    rooms = st.number_input("Pièces minimum", min_value=0, max_value=6, value=0, step=1)

    quartier = st.selectbox(
        "Quartier / Secteur",
        ["Toulon (tous)", "Mourillon", "Cap Brun", "Centre-Ville",
         "Saint-Jean du Var", "Bazeilles", "Ste Anne", "Beaulieu",
         "La Serinette", "Pont du Las"]
    )

    st.session_state.criteria = {
        "budget": budget,
        "surface_min": surface if surface > 0 else None,
        "rooms_min": rooms if rooms > 0 else None,
        "location": quartier.replace("Toulon (tous)", "toulon").lower(),
    }

    st.markdown("---")

    # Quick suggest buttons
    st.markdown("### 💡 Questions types")
    suggestions = [
        "Appartement T3 pas cher à Toulon",
        "Maison avec jardin sous 400k€",
        "Biens sous-évalués au Mourillon",
        "Comparer T2 et T3 en centre-ville",
    ]
    for s in suggestions:
        if st.button(s, key=f"sug_{s}", use_container_width=True):
            st.session_state["pending_prompt"] = s

    st.markdown("---")

    # PDF download section
    if st.session_state.last_properties:
        st.markdown("### 📄 Rapport PDF")
        st.write(f"{len(st.session_state.last_properties)} bien(s) dans la sélection")

        if st.button("📥 Générer le rapport", use_container_width=True):
            with st.spinner("Génération du rapport..."):
                _generate_pdf()

        if st.session_state.pdf_path:
            try:
                with open(st.session_state.pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="⬇️ Télécharger le PDF",
                    data=pdf_bytes,
                    file_name=f"nidbot_rapport_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except FileNotFoundError:
                st.error("Fichier PDF introuvable, regénérez.")

    st.markdown("---")
    if st.button("🗑️ Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_properties = []
        st.session_state.pdf_ready = False
        st.session_state.pdf_path = None
        st.rerun()


# ======================================================
# ================== MAIN UI ==========================
# ======================================================


# Header
st.markdown("""
<div class="nid-header">
    <h1>🏠 NidBot — Conseiller Immobilier IA</h1>
    <p>Spécialiste du marché toulonnais · Disponible 24h/24 · Données DVF + annonces en temps réel</p>
</div>
""", unsafe_allow_html=True)

# Welcome message if empty
if not st.session_state.messages:
    st.markdown("""
    <div style="background:white; border-radius:12px; padding:20px; text-align:center; color:#1B2B4B; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
        <h3 style="color:#E8714A;">Bonjour ! Je suis NidBot 👋</h3>
        <p>Votre conseiller immobilier IA, spécialisé dans le marché toulonnais.</p>
        <p>Je peux vous aider à :</p>
        <p>🔍 Trouver des biens selon votre budget &nbsp;|&nbsp; 
           📊 Identifier les opportunités sous-évaluées &nbsp;|&nbsp;
           📄 Générer un rapport PDF de vos sélections</p>
        <p style="color:#888; font-size:13px;">Commencez par décrire ce que vous cherchez ci-dessous !</p>
    </div>
    """, unsafe_allow_html=True)

# Chat history
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">{msg["content"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bot">{msg["content"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)

            # Show property cards if any
            props = msg.get("properties", [])
            if props:
                st.markdown(f"**{len(props)} bien(s) trouvé(s) :**")
                cols = st.columns(min(len(props), 2))
                for i, prop in enumerate(props):
                    with cols[i % 2]:
                        render_property_card(prop, i + 1)

# ---- Input ----
st.markdown("<br>", unsafe_allow_html=True)

# Handle suggestion click
if "pending_prompt" in st.session_state:
    pending = st.session_state.pop("pending_prompt")
    send_message(pending)
    st.rerun()

# Chat input
user_input = st.chat_input("Décrivez votre recherche... ex: T3 moins de 300k€ au Mourillon")
if user_input:
    send_message(user_input)
    st.rerun()