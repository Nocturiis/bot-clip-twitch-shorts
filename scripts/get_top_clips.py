import requests
import os
import json
import sys
from datetime import datetime, timedelta, timezone

# Twitch API credentials from GitHub Secrets
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ERREUR: TWITCH_CLIENT_ID ou TWITCH_CLIENT_SECRET non définis.")
    sys.exit(1)

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_URL = "https://api.twitch.tv/helix/clips"

# --- PARAMÈTRES DE FILTRAGE ET DE SÉLECTION POUR LES SHORTS ---

# NOUVELLE OPTION DE CONFIGURATION :
# Si TRUE, le script privilégiera strictement les clips de BROADCASTER_IDS avant d'ajouter des clips de GAME_IDS.
# Si FALSE, tous les clips (broadcasters et jeux) seront collectés puis triés globalement par vues.
PRIORITIZE_BROADCASTERS_STRICTLY = False

# NOUVEAU PARAMÈTRE : Nombre maximal de clips par streamer dans la sélection finale (pour éviter qu'un seul streamer domine si beaucoup de clips sont éligibles).
MAX_CLIPS_PER_BROADCASTER_IN_FINAL_SELECTION = 1 # Pour un short unique, on veut généralement 1 clip max par streamer par exécution

# Liste des IDs de jeux pour lesquels vous voulez récupérer des clips.
GAME_IDS = [
    "509670",        # Just Chatting
    "21779",         # League of Legends
    "32982",         # Grand Theft Auto V
    "512965",        # VALORANT
    "518018",        # Minecraft
    "513143",        # Fortnite
    "32982",         # Grand Theft Auto V
    "32399",         # Counter-Strike
    "511224",        # Apex Legends
    "506520",        # Dota 2
    "490422",        # Dead by Daylight
    "514873",        # Call of Duty: Warzone
    "65768",         # Rocket League
    "518883",        # EA Sports FC 24
    "180025139",     # Mario Kart 8 Deluxe
    "280721",        # Teamfight Tactics
    "488427",        # World of Warcraft
    "1467408070",    # Rust
    "32213",         # Hearthstone
    "138585",        # Chess
    "493306",        # Overwatch 2
    "509660",        # Special Events
    "1063683693",    # Pokémon Scarlet and Violet
    "1678120671",    # Baldur's Gate 3
    "27471",         # osu!
    "507316",        # Phasmophobia
    "19326",         # The Elder Scrolls V: Skyrim
    "512710",        # Fall Guys
    "1285324545",    # Lethal Company
    # Ajoutez d'autres IDs si nécessaire
]

# Liste des IDs de streamers francophones populaires.
BROADCASTER_IDS = [
    "80716629",      # Inoxtag
    "737048563",     # Anyme023"
    "52130765",      # Squeezie (chaîne principale)
    "22245231",      # SqueezieLive (sa chaîne secondaire pour le live)
    "41719107",      # ZeratoR
    "24147592",      # Gotaga
    "134966333",     # Kameto
    "737048563",     # AmineMaTue
    "496105401",     # byilhann
    "887001013",     # Nico_la
    "60256640",      # Flamby
    "253195796",     # helydia
    "175560856",     # Hctuan
    "57404419",      # Ponce
    "38038890",      # Antoine Daniel
    "48480373",      # MisterMV
    "19075728",      # Sardoche
    "54546583",      # Locklear
    "50290500",      # Domingo
    "57402636",      # RebeuDeter
    "47565457",      # Joyca
    "153066440",     # Michou
    "41487980",      # Pauleta_Twitch (Pfut)
    "31429949",      # LeBouseuh
    "46296316",      # Maghla
    "49896798",      # Chowh1
    "49749557",      # Jiraya
    "53696803",      # Wankil Studio (Laink et Terracid - chaîne principale)
    "72366922",      # Laink (ID individuel, généralement couvert par Wankil Studio)
    "129845722",     # Terracid (ID individuel, généralement couvert par Wankil Studio)
    "51950294",      # Mynthos
    "53140510",      # Etoiles
    "134812328",     # LittleBigWhale
    "180237751",     # Mister V (l'artiste/youtubeur, différent de MisterMV)
    "55787682",      # Shaunz
    "142436402",     # Ultia
    "20875990",      # LCK_France (pour les clips de la ligue de LoL française)
    # Ajoutez d'autres IDs vérifiés ici
]

# --- NOUVEAU PARAMÈTRE : Langue du clip ---
CLIP_LANGUAGE = "fr" # Code ISO 639-1 pour le français

# PARAMÈTRES POUR LA DURÉE CUMULÉE MINIMALE ET MAXIMALE DU SHORT FINAL
MIN_VIDEO_DURATION_SECONDS = 40  # Minimum 40 secondes pour un Short
MAX_VIDEO_DURATION_SECONDS = 60  # Maximum 60 secondes pour un Short

# --- FIN PARAMÈTRES ---

def get_twitch_access_token():
    """Gets an application access token for Twitch API."""
    print("🔑 Récupération du jeton d'accès Twitch...")
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(TWITCH_AUTH_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()
        print("✅ Jeton d'accès Twitch récupéré.")
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération du jeton d'accès Twitch : {e}")
        sys.exit(1)

def fetch_clips(access_token, params, source_type, source_id):
    """Helper function to fetch clips and handle errors."""
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(TWITCH_API_URL, headers=headers, params=params)
        response.raise_for_status()
        clips_data = response.json()
        
        if not clips_data.get("data"):
            print(f"  ⚠️ Aucune donnée de clip trouvée pour {source_type} {source_id} dans la période spécifiée.")
            return []

        collected_clips = []
        for clip in clips_data.get("data", []):
            collected_clips.append({
                "id": clip.get("id"),
                "url": clip.get("url"),
                "embed_url": clip.get("embed_url"),
                "thumbnail_url": clip.get("thumbnail_url"),
                "title": clip.get("title"),
                # CORRECTION ICI: Utilise "view_count" au lieu de "viewer_count"
                "viewer_count": clip.get("view_count", 0), 
                "broadcaster_id": clip.get("broadcaster_id"),
                "broadcaster_name": clip.get("broadcaster_name"),
                "game_name": clip.get("game_name"),
                "created_at": clip.get("created_at"),
                "duration": float(clip.get("duration", 0.0)),
                "language": clip.get("language")
            })
        return collected_clips
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des clips Twitch pour {source_type} {source_id} : {e}")
        if response.content:
            print(f"    Contenu de la réponse API Twitch: {response.content.decode()}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de décodage JSON pour {source_type} {source_id}: {e}")
        if response.content:
            print(f"    Contenu brut de la réponse: {response.content.decode()}")
        return []

def select_next_short_clip(access_token, num_clips_per_source=100, days_ago=1, already_published_clip_ids=None):
    """
    Fetches and selects the best available clip for a YouTube Short,
    avoiding previously published clips and respecting duration constraints.
    Returns the selected clip (dict) or None if no suitable clip is found.
    """
    if already_published_clip_ids is None:
        already_published_clip_ids = []

    print(f"📊 Recherche du prochain clip pour un Short (40-60s) pour les dernières {days_ago} jour(s)...")
    print(f"Clips déjà publiés aujourd'hui: {len(already_published_clip_ids)} IDs")
            
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
            
    seen_clip_ids = set(already_published_clip_ids) # Utilise un set pour une recherche rapide des doublons

    all_potential_clips = []

    # --- Phase de collecte ---
    # Collecte tous les clips des broadcasters prioritaires
    print("\n--- Collecte des clips des streamers prioritaires ---")
    for broadcaster_id in BROADCASTER_IDS:
        print(f"  - Recherche de clips pour le broadcaster_id: {broadcaster_id}")
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "broadcaster_id": broadcaster_id,
            "language": CLIP_LANGUAGE
        }
        clips = fetch_clips(access_token, params, "broadcaster_id", broadcaster_id)
        for clip in clips:
            if clip["id"] not in seen_clip_ids:
                all_potential_clips.append(clip)
                seen_clip_ids.add(clip["id"]) # Ajoute à 'seen' pour éviter les doublons globaux
    print(f"✅ Collecté {len(all_potential_clips)} clips uniques de streamers prioritaires (hors déjà publiés).")

    # Collecte tous les clips des jeux (excluant ceux déjà vus des broadcasters et déjà publiés)
    print("\n--- Collecte des clips des jeux spécifiés ---")
    for game_id in GAME_IDS:
        print(f"  - Recherche de clips pour le game_id: {game_id}")
        params = {
            "first": num_clips_per_source,
            "started_at": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sort": "views",
            "game_id": game_id,
            "language": CLIP_LANGUAGE
        }
        clips = fetch_clips(access_token, params, "game_id", game_id)
        for clip in clips:
            if clip["id"] not in seen_clip_ids:
                all_potential_clips.append(clip)
                seen_clip_ids.add(clip["id"])
    print(f"✅ Collecté {len(all_potential_clips)} clips uniques au total (streamers + jeux, hors déjà publiés).")

    # Filtrer et trier pour la sélection finale du Short
    eligible_clips = []
    
    # 1. Filtrer par langue (sécurité) et par durée
    for clip in all_potential_clips:
        if (clip.get('language') == CLIP_LANGUAGE and
            MIN_VIDEO_DURATION_SECONDS <= clip.get('duration', 0.0) <= MAX_VIDEO_DURATION_SECONDS):
            eligible_clips.append(clip)
    
    if not eligible_clips:
        print("⚠️ Aucun clip éligible (durée entre 40 et 60s, non publié) trouvé.")
        return None

    # 2. Appliquer la logique de priorisation des streamers et la limite par streamer
    final_candidates = []
    clips_added_per_broadcaster_temp = {} # Temporel pour cette exécution de sélection

    if PRIORITIZE_BROADCASTERS_STRICTLY:
        print("\nMode de sélection: PRIORITAIRE (streamers d'abord).")
        sorted_priority_clips = sorted([c for c in eligible_clips if c.get('broadcaster_id') in BROADCASTER_IDS], 
                                       key=lambda x: x.get('viewer_count', 0), reverse=True)
        
        for clip in sorted_priority_clips:
            broadcaster_id = clip.get('broadcaster_id')
            if clips_added_per_broadcaster_temp.get(broadcaster_id, 0) < MAX_CLIPS_PER_BROADCASTER_IN_FINAL_SELECTION:
                final_candidates.append(clip)
                clips_added_per_broadcaster_temp[broadcaster_id] = clips_added_per_broadcaster_temp.get(broadcaster_id, 0) + 1
            # On ne break pas ici car on peut avoir plusieurs streamers prioritaires

        # Ajouter les clips de jeux si besoin, en respectant aussi les limites par streamer
        sorted_game_clips = sorted([c for c in eligible_clips if c.get('broadcaster_id') not in BROADCASTER_IDS],
                                   key=lambda x: x.get('viewer_count', 0), reverse=True)
        for clip in sorted_game_clips:
            broadcaster_id = clip.get('broadcaster_id')
            if clips_added_per_broadcaster_temp.get(broadcaster_id, 0) < MAX_CLIPS_PER_BROADCASTER_IN_FINAL_SELECTION:
                final_candidates.append(clip)
                clips_added_per_broadcaster_temp[broadcaster_id] = clips_added_per_broadcaster_temp.get(broadcaster_id, 0) + 1
    else: # Logique classique: tout trier par vues, puis appliquer la limite par streamer
        print("\nMode de sélection: CLASSIQUE (tous les clips triés par vues).")
        sorted_all_clips = sorted(eligible_clips, key=lambda x: x.get('viewer_count', 0), reverse=True)
        
        for clip in sorted_all_clips:
            broadcaster_id = clip.get('broadcaster_id')
            if clips_added_per_broadcaster_temp.get(broadcaster_id, 0) < MAX_CLIPS_PER_BROADCASTER_IN_FINAL_SELECTION:
                final_candidates.append(clip)
                clips_added_per_broadcaster_temp[broadcaster_id] = clips_added_per_broadcaster_temp.get(broadcaster_id, 0) + 1
            # On ne break pas car on veut le meilleur candidat général selon les vues et limites par streamer

    # Trier les candidats finaux une dernière fois par vues pour s'assurer que le "meilleur" est en tête
    final_candidates.sort(key=lambda x: x.get('viewer_count', 0), reverse=True)

    if final_candidates:
        selected_clip = final_candidates[0]
        print("\n--- CLIP SÉLECTIONNÉ POUR LE SHORT ---")
        print(f"Title: {selected_clip.get('title', 'N/A')}")
        print(f"Broadcaster: {selected_clip.get('broadcaster_name', 'N/A')}")
        print(f"Views: {selected_clip.get('viewer_count', 0)}")
        print(f"Duration: {selected_clip.get('duration', 'N/A')}s")
        print(f"Language: {selected_clip.get('language', 'N/A')}")
        print(f"URL: {selected_clip.get('url', 'N/A')}")
        print("---------------------------------------\n")
        return selected_clip
    else:
        print("⚠️ Aucun clip adapté pour un Short n'a pu être sélectionné (tous les clips éligibles étaient déjà publiés ou ne respectaient pas les contraintes de durée/streamer).")
        return None

if __name__ == "__main__":
    token = get_twitch_access_token()
    if token:
        # EXEMPLE D'UTILISATION :
        # Pour simuler l'historique, vous chargeriez ceci depuis un fichier
        # Par exemple, pour le premier run de la journée, cette liste serait vide.
        # Pour les runs suivants, elle contiendrait les IDs des clips déjà publiés.
        # Après la publication réussie d'un clip, vous devriez ajouter son ID à cette liste et la sauvegarder.
        
        # Charger l'historique (simulé ici)
        published_clips_log_path = os.path.join("data", "published_shorts_history.json")
        current_published_ids = []
        if os.path.exists(published_clips_log_path):
            try:
                with open(published_clips_log_path, "r", encoding="utf-8") as f:
                    # Assurez-vous que le fichier ne contient pas d'anciennes entrées si vous voulez une rotation quotidienne
                    # Ici, pour la démo, on charge tout. Dans un vrai cas, filtrez par date.
                    data = json.load(f)
                    # Supposons que l'historique est un dictionnaire par jour ou une liste d'IDs récents
                    # Pour simplifier, on prend juste les IDs d'une liste plate
                    if isinstance(data, list):
                        current_published_ids = data
                    elif isinstance(data, dict) and "clips" in data:
                        current_published_ids = [c["id"] for c in data["clips"]]
            except json.JSONDecodeError:
                print("⚠️ Fichier d'historique des publications corrompu ou vide. Création d'un nouveau.")
                current_published_ids = []

        selected_clip = select_next_short_clip(token, 
                                               num_clips_per_source=200, # Augmente le nombre de clips à fetch
                                               days_ago=1, # Recherche sur le dernier jour pour "le plus vu du jour"
                                               already_published_clip_ids=current_published_ids)

        if selected_clip:
            print("\n✅ Un clip a été sélectionné avec succès pour le Short.")
            # Ici, vous ajouteriez la logique pour:
            # 1. Télécharger le clip (ex: en utilisant yt-dlp)
            # 2. (Optionnel) Découper le clip si sa durée est > MAX_VIDEO_DURATION_SECONDS (nécessite ffmpeg/moviepy)
            # 3. Uploader le clip sur YouTube (nécessite l'API YouTube Data v3)
            
            # Après un upload réussi, vous devez ajouter l'ID du clip à votre historique et le sauvegarder.
            # Exemple:
            # current_published_ids.append(selected_clip["id"])
            # with open(published_clips_log_path, "w", encoding="utf-8") as f:
            #     json.dump(current_published_ids, f, ensure_ascii=False, indent=2)
            # print(f"Clip {selected_clip['id']} ajouté à l'historique des publications.")
        else:
            print("\n❌ Aucun clip approprié n'a pu être trouvé pour le Short cette fois.")