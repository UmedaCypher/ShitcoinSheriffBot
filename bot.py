import os
import time
import requests
import telegram
import asyncio
import json

# --- CONFIGURATION SÉCURISÉE ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
BIRDEYE_API_KEY = os.environ.get("BIRDEYE_API_KEY")

# --- MÉMOIRE DU SHÉRIF ---
tokens_deja_vus = set()

# --- CONSTANTES ---
PATROL_INTERVAL_SECONDS = 300  # 5 minutes

# --- FONCTIONS ---

async def envoyer_alerte_telegram(message):
    """ Envoie un message Telegram en format HTML. """
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERREUR : BOT_TOKEN ou CHANNEL_ID non configuré.")
        return
    bot = telegram.Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=int(CHANNEL_ID),
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print(f"Alerte envoyée avec succès pour le message : {message[:30]}...")
    except Exception as e:
        print(f"Erreur lors de l'envoi du message Telegram: {e}")

def get_tokens_from_birdeye():
    """ Tente de récupérer les tokens récents depuis Birdeye. """
    print("Appel de l'informateur principal (Birdeye)...")
    if not BIRDEYE_API_KEY:
        print("ERREUR: Clé API Birdeye non configurée.")
        return None
        
    api_url = "https://api.birdeye.so/defi/tokenlist"
    headers = {
        "X-API-KEY": BIRDEYE_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    }
    params = {"sort_by": "creationTime", "sort_type": "desc", "offset": 0, "limit": 50}
    
    try:
        response = requests.get(url=api_url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            tokens = data.get('data', {}).get('tokens', [])
            print(f"Succès de Birdeye ! {len(tokens)} tokens trouvés.")
            return tokens
        return []
    except requests.exceptions.RequestException as e:
        print(f"Échec de l'informateur Birdeye : {e}")
        return None

def get_tokens_from_dexscreener():
    """ Tente de récupérer les tokens récents depuis DexScreener (Plan B). """
    print("Birdeye ne répond pas. Appel de l'adjoint (DexScreener)...")
    # CORRECTION: On demande les dernières paires sur Solana, on filtrera "pump" ensuite.
    api_url = "https://api.dexscreener.com/latest/pairs/solana"
    try:
        response = requests.get(url=api_url, timeout=20)
        response.raise_for_status()
        data = response.json()
        pairs = data.get('pairs', [])
        
        # On filtre pour ne garder que les paires de pump.fun
        pump_pairs = [p for p in pairs if p.get('dexId') == 'pump']
        print(f"Succès de DexScreener ! {len(pump_pairs)} paires pump.fun trouvées.")
        
        tokens = []
        for pair in pump_pairs:
            if pair.get('baseToken'):
                tokens.append({
                    'address': pair['baseToken'].get('address'),
                    'name': pair['baseToken'].get('name'),
                    'symbol': pair['baseToken'].get('symbol'),
                    'data_source': 'DexScreener'
                })
        return tokens
    except requests.exceptions.RequestException as e:
        print(f"Échec de l'adjoint DexScreener : {e}")
        return None

async def patrouille_du_sherif():
    """ Le cycle de travail principal du bot. """
    global tokens_deja_vus
    print("Début de la patrouille...")
    
    tokens_recents = get_tokens_from_birdeye()
    
    if tokens_recents is None: # Si Birdeye a échoué
        tokens_recents = get_tokens_from_dexscreener()

    if tokens_recents is None: # Si les deux ont échoué
        print("Les deux informateurs sont silencieux. Fin de la patrouille.")
        return

    nouveaux_suspects = []
    for token in tokens_recents:
        adresse = token.get('address')
        if adresse and adresse not in tokens_deja_vus:
            nouveaux_suspects.append(token)

    if nouveaux_suspects:
        print(f"{len(nouveaux_suspects)} nouveaux suspects identifiés !")
        
        print("\n--- RAPPORT D'ENQUÊTE COMPLET SUR LE PREMIER SUSPECT ---")
        print(json.dumps(nouveaux_suspects[0], indent=2))
        print("---------------------------------------------------\n")

        for suspect in nouveaux_suspects:
            adresse = suspect.get("address")
            nom = suspect.get('name', 'N/A')
            symbole = suspect.get('symbol', 'N/A')
            source = suspect.get('data_source', 'Birdeye')
            
            pump_fun_link = f"https://pump.fun/{adresse}"
            message = (f"<b>🔫 Nouveau Suspect ({source}) 🔫</b>\n\n"
                       f"<b>Nom :</b> {nom} (${symbole})\n"
                       f"<b>Adresse :</b> <code>{adresse}</code>\n\n"
                       f"👉 <a href='{pump_fun_link}'>Inspecter le suspect</a>")
            
            await envoyer_alerte_telegram(message)
            tokens_deja_vus.add(adresse)
            await asyncio.sleep(1)
    else:
        print("Aucun nouveau suspect cette fois-ci.")

# --- Boucle Principale ---
if __name__ == "__main__":
    print("Le Shérif démarre son service de patrouille...")
    while True:
        try:
            asyncio.run(patrouille_du_sherif())
        except Exception as e:
            print(f"Une erreur critique est survenue dans la boucle principale: {e}")
        
        print(f"Patrouille terminée. Prochaine ronde dans {PATROL_INTERVAL_SECONDS / 60} minutes.")
        time.sleep(PATROL_INTERVAL_SECONDS)

