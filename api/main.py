from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import re
import logging
from .property_service import fetch_properties
from .pdf_service import generate_pdf_report

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ======================================================
# ================== HELPERS ==========================
# ======================================================

def extract_budget(prompt: str) -> float | None:
    # Match patterns like "450000", "450 000", "450k", "450K€"
    match = re.search(r"(\d[\d\s]*)\s*(?:k€|k|000\s*€|€|euros?)?", prompt.lower())
    if match:
        raw = match.group(1).replace(" ", "")
        val = float(raw)
        # If it looks like "450k" shorthand
        if val < 2000:
            val *= 1000
        if 50000 <= val <= 2000000:
            return val
    return None


def extract_surface(prompt: str) -> float | None:
    match = re.search(r"(\d+)\s*(?:m²|m2|metres?|mètres?)", prompt.lower())
    return float(match.group(1)) if match else None


def extract_rooms(prompt: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:pièces?|rooms?|chambres?)", prompt.lower())
    return int(match.group(1)) if match else None


def extract_location(prompt: str) -> str:
    """Extract neighborhood or city from prompt"""
    patterns = [
        r"\bà\s+([A-Za-zÀ-ÿ\-\s]+?)(?:\s+(?:avec|pour|budget|moins|plus|environ|autour)|$)",
        r"\bdans\s+(?:le\s+quartier\s+(?:de\s+)?)?([A-Za-zÀ-ÿ\-\s]+?)(?:\s+(?:avec|pour|budget|moins|plus)|$)",
        r"\bquartier\s+(?:de\s+)?([A-Za-zÀ-ÿ\-\s]+?)(?:\s+(?:avec|pour|budget|moins|plus)|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return match.group(1).strip()
    return "Toulon"  # default


# ======================================================
# ================== APP ==============================
# ======================================================

app = FastAPI(title="NidBot — Conseiller Immobilier IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama:11434")
OLLAMA_BASE_URL = OLLAMA_HOST if OLLAMA_HOST.startswith("http") else f"http://{OLLAMA_HOST}"
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = """Tu es NidBot, un conseiller immobilier expert spécialisé dans le marché toulonnais.
Tu aides des jeunes couples primo-accédants avec un budget maximum de 450 000€.
Tu es chaleureux, professionnel et tu argumentes tes recommandations avec des données concrètes.
Tu parles uniquement de l'immobilier. Pour tout autre sujet, redirige poliment vers ta spécialité.
Quand tu présentes des biens, structure ta réponse clairement avec les points forts et les arguments.
"""


class PromptRequest(BaseModel):
    prompt: str
    conversation_history: list[dict] = []


class AIResponse(BaseModel):
    response: str
    properties: list[dict] = []
    pdf_available: bool = False


class PDFRequest(BaseModel):
    properties: list[dict]
    conversation_summary: str
    client_criteria: dict = {}


@app.get("/")
def health():
    return {"status": "OK", "service": "NidBot API"}


# ======================================================
# ================== CHAT =============================
# ======================================================

@app.post("/chat", response_model=AIResponse)
def chat_with_nidbot(data: PromptRequest):
    try:
        return _chat_impl(data)
    except Exception as e:
        logger.error(f"Unhandled error in chat: {str(e)}", exc_info=True)
        return AIResponse(
            response=f"Une erreur s'est produite: {str(e)}",
            properties=[],
            pdf_available=False
        )


def _chat_impl(data: PromptRequest) -> AIResponse:

    prompt_lower = data.prompt.lower()

    # Keywords that trigger property search
    property_keywords = [
        "appartement", "maison", "bien", "biens", "propriété", "logement",
        "acheter", "achat", "acquérir", "acquis",
        "cherche", "recherche", "trouver", "trouve",
        "budget", "prix", "coût", "€", "euros",
        "pièces", "chambres", "surface", "m²", "m2",
        "quartier", "toulon", "var", "mourillon", "cap brun", "saint-jean",
        "recommande", "recommandation", "conseille", "conseil",
        "primo-accédant", "primo accédant", "premier achat",
        "sous-évalué", "bon prix", "opportunité",
    ]

    non_property_keywords = [
        "météo", "sport", "recette", "cuisine", "politique", "news",
        "actualité", "blague", "jeu", "musique",
    ]

    is_property_request = any(k in prompt_lower for k in property_keywords)
    is_off_topic = any(k in prompt_lower for k in non_property_keywords)

    if is_off_topic and not is_property_request:
        return AIResponse(
            response=(
                "Je suis NidBot, votre conseiller immobilier spécialisé sur le marché toulonnais 🏠\n\n"
                "Je ne suis pas en mesure de vous aider sur ce sujet, mais je serais ravi de vous accompagner "
                "dans votre recherche immobilière !\n\n"
                "Par exemple, je peux vous aider à :\n"
                "• Trouver des appartements ou maisons à Toulon selon votre budget\n"
                "• Analyser les prix par quartier\n"
                "• Identifier les biens sous-évalués\n"
                "• Comparer des opportunités d'achat\n\n"
                "Qu'est-ce qui vous ferait plaisir comme recherche ?"
            )
        )

    # ---------- EXTRACT CRITERIA ----------
    budget = extract_budget(data.prompt) or 450000
    surface = extract_surface(data.prompt)
    rooms = extract_rooms(data.prompt)
    location = extract_location(data.prompt)
    
    logger.info(f"Extracted criteria - location: {location}, budget: {budget}, surface: {surface}, rooms: {rooms}")

    # ---------- FETCH PROPERTIES ----------
    properties = []
    if is_property_request:
        try:
            properties = fetch_properties(
                location=location,
                budget_max=budget,
                surface_min=surface,
                rooms_min=rooms,
                top_n=5
            )
            logger.info(f"Found {len(properties)} properties")
        except Exception as e:
            logger.error(f"Error fetching properties: {str(e)}", exc_info=True)
            properties = []

    # Si on a des properties, on va toujours retourner une réponse structurée
    if properties and not is_off_topic:
        ai_response = _format_fallback_response(properties, budget, location)
        # On essaie quand même d'avoir une réponse Ollama pour un meilleur texte
        try:
            # Build context with properties
            context = "\n\nAnnonces immobilières correspondantes :\n"
            for i, p in enumerate(properties, 1):
                context += (
                    f"\n[Bien {i}]\n"
                    f"Adresse : {p['address']}, {p['neighborhood']}, Toulon\n"
                    f"Type : {p['type']} | Surface : {p['surface']}m² | Pièces : {p['rooms']}\n"
                    f"Prix : {p['price']:,.0f}€ ({p['price_per_m2']:,.0f}€/m²)\n"
                    f"Prix marché quartier : {p['market_price_per_m2']:,.0f}€/m² "
                    f"({'SOUS-ÉVALUÉ ✓' if p['is_undervalued'] else 'Dans la moyenne'})\n"
                    f"Source : {p['source']} | Référence : {p['ref']}\n"
                )
            context += "\nBase ta réponse sur ces biens réels. Argumente tes recommandations."
            
            # Build history
            history_text = ""
            for msg in data.conversation_history[-6:]:
                role = "Utilisateur" if msg["role"] == "user" else "NidBot"
                history_text += f"{role}: {msg['content']}\n"

            full_prompt = f"{SYSTEM_PROMPT}\n\n{history_text}Utilisateur: {data.prompt}{context}\n\nNidBot:"

            logger.info(f"Calling Ollama at {OLLAMA_URL}")
            resp = requests.post(
                OLLAMA_URL,
                json={"model": MODEL_NAME, "prompt": full_prompt, "stream": False},
                timeout=60
            )
            if resp.status_code == 200:
                ai_response = resp.json().get("response", ai_response).strip()
                logger.info("Got response from Ollama")
        except Exception as e:
            logger.warning(f"Ollama optional enhancement failed: {str(e)}")
            # Use fallback response we already prepared
            pass
        
        return AIResponse(
            response=ai_response,
            properties=properties,
            pdf_available=True
        )
    
    # Si pas de propriétés trouvées or off-topic, retourner un message par défaut
    return AIResponse(
        response=(
            "Je n'ai pas trouvé de biens correspondant à votre recherche "
            "ou votre recherche est en dehors de ma spécialité (marché immobilier toulonnais).\n\n"
            "Je peux vous aider avec :\n"
            "• Recherches immobilières à Toulon\n"
            "• Analyses de biens spécifiques\n"
            "• Conseils sur le marché local\n\n"
            "Réessayez avec une recherche plus précise sur Toulon!"
        ),
        properties=[],
        pdf_available=False
    )


def _format_fallback_response(properties: list, budget: float, location: str) -> str:
    """Structured fallback when Ollama is unavailable"""
    best = properties[0]
    response = (
        f"🏠 J'ai trouvé {len(properties)} bien(s) correspondant à votre recherche "
        f"autour de {location} avec un budget de {budget:,.0f}€ :\n\n"
        f"**⭐ Meilleure opportunité :**\n"
        f"📍 {best['address']}, {best['neighborhood']}\n"
        f"💰 {best['price']:,.0f}€ — {best['price_per_m2']:,.0f}€/m²\n"
        f"📐 {best['surface']}m² | {best['rooms']} pièces\n"
    )
    if best.get("is_undervalued"):
        response += f"✅ **Bien sous-évalué** : prix inférieur au marché du quartier ({best['market_price_per_m2']:,.0f}€/m²)\n"

    if len(properties) > 1:
        response += "\n**Autres biens :**\n"
        for p in properties[1:]:
            response += f"• {p['address']} — {p['price']:,.0f}€ ({p['surface']}m²)\n"

    return response


# ======================================================
# ================== PDF GENERATION ==================
# ======================================================

@app.post("/generate-pdf")
def create_pdf_report(data: PDFRequest):
    try:
        pdf_path = generate_pdf_report(
            properties=data.properties,
            conversation_summary=data.conversation_summary,
            client_criteria=data.client_criteria
        )
        return {"status": "ok", "path": pdf_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/pdf/{filename}")
def download_pdf(filename: str):
    from fastapi.responses import FileResponse
    path = f"/tmp/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="application/pdf", filename=filename)
    return {"error": "File not found"}