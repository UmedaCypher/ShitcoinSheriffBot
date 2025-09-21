import telegram
import asyncio
import os
import time
import requests # La librairie pour faire des appels API
import json # Ajout de la librairie pour un affichage propre

# --- CONFIGURATION SÉCURISÉE ---
# Ces variables sont lues depuis l'environnement de Render.
# Assurez-vous de les avoir configurées dans l'onglet "Environment" de votre service.
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
BIRDEYE_API_KEY = os.environ.get("BIRDEYE_API_KEY") 
# --- FIN DE LA CONFIGURATION ---

# --- MÉMOIRE ET PARAMÈTRES DU SHÉRIF ---
# Garde en mémoire les tokens pour lesquels une alerte a déjà été envoyée
# pour éviter les doublons.
tokens_deja_vus = set()

async def send_telegram_message(message_text):
    """
    Envoie un message Telegram en format HTML.
    """
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERREUR : BOT_TOKEN ou CHANNEL_ID non configuré.")
        return
    bot = telegram.Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=int(CHANNEL_ID), 
            text=message_text,
            parse_mode="HTML",
            disable_web_page_preview=True # Pour que les liens n'affichent pas d'aperçu moche
        )
        print("Message de notification envoyé avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi du message Telegram: {e}")

def get_new_tokens_from_birdeye():
    """
    Appelle l'API de Birdeye pour trouver les nouveaux tokens sur pump.fun.
    C'est le "Scanner" du Shérif.
    """
    print("Appel de l'API Birdeye pour les nouveaux tokens pump.fun...")
    if not BIRDEYE_API_KEY:
        print("ERREUR: La variable d'environnement BIRDEYE_API_KEY n'est pas configurée sur Render.")
        return []

    # C'est l'URL de l'API de Birdeye pour les nouvelles paires ("new_pairs")
    api_url = "https://public-api.birdeye.so/defi/new_pairs"
    
    headers = {
        "X-API-KEY": BIRDEYE_API_KEY
    }
    
    # On filtre pour la blockchain Solana et la source pump.fun
    params = {
        "chain": "solana",
        "source": "pump" 
    }

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status() # Lève une erreur si la requête HTTP échoue (ex: 401, 404, 500)
        data = response.json()
        
        if data.get('success'):
            items = data.get('data', {}).get('items', [])
            print(f"Succès ! {len(items)} tokens trouvés dans la dernière patrouille.")
            return items
        else:
            print(f"L'API Birdeye a retourné une erreur: {data.get('message')}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API Birdeye: {e}")
        return []

async def patrouille_du_sherif():
    """
    Le cycle de travail principal du bot : il récupère, analyse et alerte.
    """
    print("Début de la patrouille...")
    nouveaux_tokens = get_new_tokens_from_birdeye()
    
    # ---- NOUVELLE LOGIQUE POUR L'ANALYSE ----
    a_imprime_un_rapport = False
    # ----------------------------------------

    for token in nouveaux_tokens:
        token_address = token.get("address") # L'adresse du contrat du token
        
        # Si le token a une adresse et qu'on ne l'a jamais vu avant
        if token_address and token_address not in tokens_deja_vus:
            
            # ---- NOUVELLE LOGIQUE POUR L'ANALYSE ----
            # On imprime le rapport complet du premier nouveau suspect trouvé
            if not a_imprime_un_rapport:
                print("\n--- RAPPORT D'ENQUÊTE COMPLET SUR LE PREMIER SUSPECT ---")
                # On utilise json.dumps pour un affichage propre et lisible
                print(json.dumps(token, indent=2))
                print("---------------------------------------------------\n")
                a_imprime_un_rapport = True
            # ----------------------------------------

            token_symbol = token.get('tokenSymbol', 'N/A')
            tx_count = token.get('txCount', 0)
            
            pump_fun_link = f"https://pump.fun/{token_address}"

            message = (f"<b>🔫 Nouveau Suspect Apperçu sur Pump.fun 🔫</b>\n\n"
                       f"<b>Nom :</b> ${token_symbol}\n"
                       f"<b>Adresse :</b> <code>{token_address}</code>\n"
                       f"<b>Transactions (5min) :</b> {tx_count}\n\n"
                       f"👉 <a href='{pump_fun_link}'>Inspecter le suspect</a>")
            
            await send_telegram_message(message)
            tokens_deja_vus.add(token_address)
            
            # Petite pause pour ne pas surcharger l'API de Telegram si on trouve beaucoup de tokens d'un coup
            await asyncio.sleep(1)

if __name__ == "__main__":
    print("Le Shérif démarre son service de patrouille...")
    # Boucle infinie pour que le bot tourne en continu
    while True:
        try:
            asyncio.run(patrouille_du_sherif())
        except Exception as e:
            print(f"Une erreur critique est survenue dans la boucle principale: {e}")
        
        print("Patrouille terminée. Prochaine ronde dans 5 minutes.")
        time.sleep(300) # Le bot se met en veille pendant 300 secondes (5 minutes)



