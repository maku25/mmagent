import os
import re
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from agent import extraire_information
from publisher import generer_post


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def extraire_tweet_lien(msg: str) -> str:
    match = re.search(r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/status/([0-9]+)", msg)
    if not match:
        return msg
    
    user, tweet_id = match.groups()
    api_url = f"https://api.fxtwitter.com/{user}/status/{tweet_id}"

    resp = requests.get(api_url, timeout=8)
    if resp.status_code == 200:
        tweet_data = resp.json().get("tweet", {})
        texte_tweet = tweet_data.get("text", "")
        auteur = tweet_data.get("author", {}).get("name", "")
        if texte_tweet:
            return f"Tweet de {auteur} : {texte_tweet}"
    raise ValueError("Impossible de récupérer le contenu de ce tweet X.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**MMAgent** 🥊\n\n"
        "Partage une news"
    )

async def traiter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text

    msg_attente = await update.message.reply_text("🧠 Analyse et rédaction en cours...")

    try:
        texte_brut = await asyncio.to_thread(extraire_tweet_lien, msg)
        donnees = await asyncio.to_thread(extraire_information, texte_brut)
        post = generer_post(donnees)

        reponse = (
            f"{post}\n\n"
            f"──────────────────\n"
            f"*Catégorie : {donnees.type_post} | Pertinence : {donnees.score_importance}/10*"
        )
        await msg_attente.edit_text(reponse)

    except Exception as e:
        await msg_attente.edit_text(f"Erreur lors du traitement : {e}")

        
if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN est manquant dans le fichier .env")

    print("Démarrage du bot Telegram MMAgent...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), traiter_message))

    app.run_polling()

