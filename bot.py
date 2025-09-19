import telegram
import asyncio
import os # On importe la librairie "os" pour lire les variables d'environnement
from flask import Flask, request

# --- CONFIGURATION SÉCURISÉE ---
# Le code va maintenant chercher les secrets dans l'environnement du serveur.
# Nous les configurerons directement sur le site de Render.
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
# --- FIN DE LA CONFIGURATION ---

# Initialise Flask
app = Flask(__name__)

async def send_telegram_message(message_text):
    """
    Envoie un message Telegram.
    """
    # Vérification pour s'assurer que les secrets ont bien été chargés
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERREUR : BOT_TOKEN ou CHANNEL_ID non configuré dans les variables d'environnement.")
        return

    bot = telegram.Bot(token=BOT_TOKEN)
    try:
        # On convertit l'ID du canal en nombre entier
        await bot.send_message(chat_id=int(CHANNEL_ID), text=message_text)
        print("Message de notification envoyé avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi du message Telegram: {e}")

# Route unique pour le webhook Helius
@app.route('/webhook', methods=['POST'])
def helius_webhook():
    print("=== NOUVELLE REQUÊTE ===")
    data = request.get_json(force=True, silent=True)
    print("JSON parsé:", data)
    
    asyncio.run(send_telegram_message("✅ Alerte ! Webhook reçu"))
    return {"status": "ok"}, 200

if __name__ == "__main__":
    print("Le serveur du Shérif est en ligne et écoute les webhooks...")
    app.run(port=5000)

