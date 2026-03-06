graph TD
    subgraph "Sources de Données"
        DVF["API DVF / data.gouv.fr (Transactions)"]
        WebScraping["GumLoop / Scraping (Annonces réelles)"]
    end

    subgraph "Couche de Données (data/)"
        DVF_File[("dvf_toulon.csv")]
        Ann_File[("annonces.csv")]
        Raw_Dir["Dossier raw/ (données brutes)"]
    end

    subgraph "Moteur d'Analyse From Scratch (analysis/)"
        Stats["stats.py (Moyenne, Médiane, Corrélation)"]
        Reg["regression.py (Modèle de prédiction de prix)"]
        Scoring["scoring.py (Score d'opportunité)"]
    end

    subgraph "Enrichissement IA"
        LLM["API OpenAI / Claude (Parsing & Résumés)"]
    end

    subgraph "Agent Conversationnel"
        Chat["Chatbot (Accompagnement 24/7)"]
    end

    subgraph "Interface Utilisateur (app/)"
        Streamlit["streamlit_app.py (Dashboard interactif)"]
    end

    subgraph "Qualité & CI/CD"
        Tests["tests/ (Unit tests avec pytest)"]
        Actions["GitHub Actions (Auto-évaluation)"]
    end

    %% Flux de données
    DVF --> DVF_File
    WebScraping --> Ann_File
    DVF_File & Ann_File --> Stats
    DVF_File & Ann_File --> Scoring
    Ann_File --> LLM
    LLM --> Scoring
    
    %% Flux Analyse vers UI
    Stats & Reg --> Streamlit
    Scoring --> Streamlit
    
    %% Flux Agent Conversationnel
    Stats & Scoring -.-> Chat
    Chat <--> Streamlit
    
    %% Utilisateur
    Streamlit --> User((Utilisateur Final))
    
    %% Lien vers les tests
    Stats & Reg -.-> Tests
    Tests -.-> Actions