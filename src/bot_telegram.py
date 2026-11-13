import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from agent import extraire_information
from publisher import generer_post


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**MMAgent** 🥊\n\n"
        "Partage une news"
    )

async def traiter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte = update.message.text

    msg_attente = await update.message.reply_text("🧠 Analyse et rédaction en cours...")

    try:
        donnees = await asyncio.to_thread(extraire_information, texte)
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

