# main.py
import sys
import os
import json
from datetime import datetime, date

# Ajouter le répertoire 'scripts' au PYTHONPATH pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

import get_top_clips
import download_clip
import process_video
import generate_metadata
import upload_youtube

# --- Chemins et configuration ---
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PUBLISHED_HISTORY_FILE = os.path.join(DATA_DIR, 'published_shorts_history.json')
# Fichiers temporaires pour le clip
RAW_CLIP_PATH = os.path.join(DATA_DIR, 'temp_raw_clip.mp4')
PROCESSED_CLIP_PATH = os.path.join(DATA_DIR, 'temp_processed_short.mp4')

# --- Fonctions utilitaires pour l'historique ---
def load_published_history():
    """Charge l'historique des clips publiés."""
    if not os.path.exists(PUBLISHED_HISTORY_FILE):
        return {}
    try:
        with open(PUBLISHED_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Fichier d'historique des publications corrompu. Création d'un nouveau.")
        return {}

def save_published_history(history_data):
    """Sauvegarde l'historique des clips publiés."""
    with open(PUBLISHED_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)

def get_today_published_ids(history_data):
    """Retourne les IDs des clips publiés aujourd'hui."""
    today_str = date.today().isoformat()
    return history_data.get(today_str, [])

def add_to_history(history_data, clip_id, youtube_id):
    """Ajoute un clip à l'historique pour la date d'aujourd'hui."""
    today_str = date.today().isoformat()
    if today_str not in history_data:
        history_data[today_str] = []
    
    # Stocke l'ID Twitch du clip et l'ID YouTube du Short
    history_data[today_str].append({"twitch_clip_id": clip_id, "youtube_short_id": youtube_id, "timestamp": datetime.now().isoformat()})
    
    # OPTIONNEL: Nettoyer l'historique des anciennes entrées (ex: plus de 7 jours)
    # old_dates = [d for d in history_data if (datetime.now().date() - datetime.fromisoformat(d).date()).days > 7]
    # for d in old_dates:
    #     del history_data[d]
    # print(f"Historique nettoyé. {len(old_dates)} anciennes entrées supprimées.")


def main():
    print("🚀 Début du workflow de publication de Short YouTube...")

    # 1. Charger l'historique des clips publiés
    history = load_published_history()
    today_published_ids = [item["twitch_clip_id"] for item in get_today_published_ids(history)]
    print(f"Clips déjà publiés aujourd'hui : {len(today_published_ids)}.")

    # 2. Récupérer le jeton d'accès Twitch
    twitch_token = get_top_clips.get_twitch_access_token()
    if not twitch_token:
        print("❌ Impossible d'obtenir le jeton d'accès Twitch. Fin du script.")
        sys.exit(1)

    # 3. Sélectionner le prochain clip à publier
    selected_clip = get_top_clips.select_next_short_clip(
        access_token=twitch_token,
        num_clips_per_source=200, # Augmenter pour avoir plus de candidats
        days_ago=1, # Chercher les clips du dernier jour
        already_published_clip_ids=today_published_ids
    )

    if not selected_clip:
        print("🤷‍♂️ Aucun nouveau clip adapté trouvé pour la publication aujourd'hui. Fin du script.")
        sys.exit(0) # Sortie normale, pas d'erreur, juste pas de contenu

    # 4. Télécharger le clip
    downloaded_file = download_clip.download_twitch_clip(selected_clip['url'], RAW_CLIP_PATH)
    if not downloaded_file:
        print("❌ Échec du téléchargement du clip. Fin du script.")
        sys.exit(1)

    # 5. Traiter/couper la vidéo pour s'assurer qu'elle est adaptée au Short
    # C'est ici que process_video.py est appelé. Si vous n'utilisez pas moviepy/ffmpeg,
    # vous pouvez simplement faire 'processed_file = downloaded_file'
    print("🎬 Traitement de la vidéo pour le format Short (découpage si nécessaire)...")
    processed_file = process_video.trim_video_for_short(downloaded_file, PROCESSED_CLIP_PATH,
                                                         max_duration_seconds=get_top_clips.MAX_VIDEO_DURATION_SECONDS)
    
    # Si le script process_video.py n'est pas utilisé ou renvoie None
    if not processed_file:
        print("⚠️ Le traitement vidéo a échoué ou n'a pas été effectué. Utilisation du fichier brut si disponible.")
        # Tentative d'utiliser le fichier brut si le traitement a échoué.
        # ATTENTION: Cela pourrait uploader un clip trop long !
        processed_file = downloaded_file 
        if os.path.getsize(processed_file) == 0: # Vérifie si le fichier brut est vide
            print("❌ Le fichier brut est vide. Impossible de continuer. Fin du script.")
            sys.exit(1)
        else:
            print(f"Utilisation du fichier brut pour l'upload : {processed_file}")


    # 6. Générer les métadonnées YouTube
    youtube_metadata = generate_metadata.generate_youtube_metadata(selected_clip)

    # 7. Authentifier et Uploader sur YouTube
    # Pour GitHub Actions, 'client_secret.json' et 'token.json' doivent être gérés via secrets.
    # La première fois, 'token.json' doit être généré localement et ensuite copié dans un secret GitHub.
    youtube_service = upload_youtube.get_authenticated_service()
    if not youtube_service:
        print("❌ Impossible d'authentifier le service YouTube. Fin du script.")
        sys.exit(1)

    youtube_video_id = upload_youtube.upload_youtube_short(youtube_service, processed_file, youtube_metadata)

    if youtube_video_id:
        print(f"🎉 Short YouTube publié avec succès ! ID: {youtube_video_id}")
        # 8. Mettre à jour l'historique des publications
        add_to_history(history, selected_clip['id'], youtube_video_id)
        save_published_history(history)
        print(f"✅ Clip '{selected_clip['id']}' ajouté à l'historique des publications.")
    else:
        print("❌ Échec de la publication du Short YouTube. Fin du script.")
        sys.exit(1)

    # 9. Nettoyage des fichiers temporaires
    print("🧹 Nettoyage des fichiers temporaires...")
    if os.path.exists(RAW_CLIP_PATH):
        os.remove(RAW_CLIP_PATH)
        print(f"  - Supprimé: {RAW_CLIP_PATH}")
    if os.path.exists(PROCESSED_CLIP_PATH):
        os.remove(PROCESSED_CLIP_PATH)
        print(f"  - Supprimé: {PROCESSED_CLIP_PATH}")

    print("✅ Workflow terminé.")

if __name__ == "__main__":
    main()