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

def extraire_lien(msg: str) -> str:
    url_match = re.search(r"(https?://[^\s]+)", msg)
    if not url_match:
        return msg
    
    url = url_match.group(1)

    x_match = re.search(r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/status/([0-9]+)", url)

    if x_match:
        user, tweet_id = x_match.groups()
        api_url = f"https://api.fxtwitter.com/{user}/status/{tweet_id}"
        resp = requests.get(api_url, timeout=8)
        if resp.status_code == 200:
            tweet_data = resp.json().get("tweet", {})
            texte_tweet = tweet_data.get("text", "")
            auteur = tweet_data.get("author", {}).get("name", "")
            if texte_tweet:
                return f"Tweet de {auteur} : {texte_tweet}"
        raise ValueError("Impossible de récupérer le contenu de ce tweet.")

    if any(dom in url for dom in ["instagram.com", "facebook.com", "fb.watch"]):
        raise ValueError(
            "Instagram et Facebook bloquent la lecture directe des liens. "
            "Envoie-moi directement une capture d'écran du post."
        )

    jina_url = f"https://r.jina.ai/{url}"
    resp = requests.get(jina_url, timeout=12)
    if resp.status_code == 200 and resp.text.strip():
        return f"Article web ({url}) :\n{resp.text[:6000]}"

    raise ValueError("Impossible de lire le contenu de cette page web.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**MMAgent** 🥊\n\n"
        "Partage une news"
    )

async def traiter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text

    msg_attente = await update.message.reply_text("🧠 Analyse et rédaction en cours...")

    try:
        texte_brut = await asyncio.to_thread(extraire_lien, msg)
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

        
async def traiter_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_attente = await update.message.reply_text("📸 Analyse de l'image en cours...")
    try:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = bytes(await photo_file.download_as_bytearray())
        
        legende = update.message.caption or ""

        donnees = await asyncio.to_thread(extraire_information, texte=legende, image=image_bytes)
        post = generer_post(donnees)

        reponse = (
            f"{post}\n\n"
            f"──────────────────\n"
            f"*Catégorie : {donnees.type_post} | Pertinence : {donnees.score_importance}/10*"
        )
        await msg_attente.edit_text(reponse)

    except Exception as e:
        await msg_attente.edit_text(f"Erreur lors de l'analyse de l'image : {e}")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN est manquant dans le fichier .env")

    print("Démarrage de MMAgent...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), traiter_message))
    app.add_handler(MessageHandler(filters.PHOTO, traiter_photo))

    app.run_polling()

