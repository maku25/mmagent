# MMAgent

Outil de veille et de rédaction automatisée pour produire des posts média prêts à publier à partir de sources web.


## Fonctionnalités

* **Veille automatique :** Recherche d'actualités sur une liste de sujets (`data/watchlist.json`) via Tavily et filtrage des doublons (`data/seen_urls.json`).
* **Rédaction à la demande :** Transformation d'un lien X (`fxTwitter`), d'un article (`Jina AI`), d'un texte ou d'une capture d'écran en post formaté.
* **Mise en page cohérente :** Extraction des infos clés avec Gemini et Pydantic, puis application de modèles prédéfinis (`prompts/templates.json`).

## Stack

Python, Google Gemini API, Pydantic, Tavily, python-telegram-bot

## Installation

1. Cloner le dépôt et installer les dépendances :
```bash
git clone [https://github.com/maku25/mmagent.git](https://github.com/maku25/mmagent.git)
cd mmagent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt


2. Créer un fichier `.env` à la racine du projet :
```env
GEMINI_API_KEY="..."
TELEGRAM_BOT_TOKEN="..."
TAVILY_API_KEY="..."
TELEGRAM_CHAT_ID="..."
```

3. Lancer l'application :
```bash
python src/bot_telegram.py
```