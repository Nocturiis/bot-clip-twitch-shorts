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
import upload_youtube # Toujours importé, même si non utilisé pour l'upload


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
    except Exception as e:
        print(f"❌ Erreur inattendue lors du chargement de l'historique : {e}")
        return {}

def save_published_history(history_data):
    """Sauvegarde l'historique des clips publiés."""
    try:
        with open(PUBLISHED_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Erreur inattendue lors de la sauvegarde de l'historique : {e}")


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
    #       del history_data[d]
    # print(f"Historique nettoyé. {len(old_dates)} anciennes entrées supprimées.")


def main():
    print("🚀 Début du workflow de publication de Short YouTube (mode débogage / sans upload)...")

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
        num_clips_per_source=50, # Augmenter pour avoir plus de candidats
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
    print("🎬 Traitement de la vidéo pour le format Short (découpage si nécessaire)...")
    processed_file = process_video.trim_video_for_short(
        input_path=downloaded_file,
        output_path=PROCESSED_CLIP_PATH,
        max_duration_seconds=get_top_clips.MAX_VIDEO_DURATION_SECONDS,
        clip_data=selected_clip,
        enable_webcam_crop=False # Mettez à True si vous voulez activer le rognage de la webcam
    )
    
    # --- DÉBUT DES NOUVELLES VÉRIFICATIONS ---
    if processed_file: # Si process_video.trim_video_for_short a renvoyé un chemin (donc succès apparent)
        if not os.path.exists(processed_file):
            print(f"❌ ERREUR MAJEURE : Le fichier traité devrait exister à {processed_file}, mais il est introuvable après traitement.")
            print("Cela indique un problème lors de l'écriture du fichier vidéo par MoviePy.")
            processed_file = None # Force le passage à l'utilisation du fichier brut ou l'arrêt
        elif os.path.getsize(processed_file) == 0:
            print(f"❌ ERREUR MAJEURE : Le fichier traité {processed_file} est vide !")
            print("Cela indique que MoviePy a créé le fichier mais n'a pas pu y écrire de données vidéo.")
            processed_file = None # Force le passage à l'utilisation du fichier brut ou l'arrêt
        else:
            print(f"✅ Fichier traité trouvé et non vide : {processed_file} (taille : {os.path.getsize(processed_file)} octets).")
    # --- FIN DES NOUVELLES VÉRIFICATIONS ---


    # Si le script process_video.py n'est pas utilisé ou renvoie None
    if not processed_file:
        print("⚠️ Le traitement vidéo a échoué ou n'a pas été effectué. Utilisation du fichier brut si disponible.")
        # Tentative d'utiliser le fichier brut si le traitement a échoué.
        # ATTENTION: Cela pourrait uploader un clip trop long !
        processed_file = downloaded_file 
        if not os.path.exists(processed_file) or os.path.getsize(processed_file) == 0: # Vérifie si le fichier brut est vide ou n'existe pas
            print("❌ Le fichier brut est vide ou n'existe pas. Impossible de continuer. Fin du script.")
            sys.exit(1)
        else:
            print(f"Utilisation du fichier brut pour l'upload : {processed_file}")


    # 6. Générer les métadonnées YouTube (toujours utile pour le débogage)
    youtube_metadata = generate_metadata.generate_youtube_metadata(selected_clip)

    print("\n--- Informations sur le Short (pour débogage) ---")
    print(f"Titre: {youtube_metadata.get('title')}")
    print(f"Description: {youtube_metadata.get('description')}")
    print(f"Tags: {', '.join(youtube_metadata.get('tags', []))}")
    print(f"Chemin de la vidéo finale: {processed_file}")
    print("-------------------------------------------------\n")

    # 7. Authentifier et Uploader sur YouTube
    # LA LIGNE SUIVANTE EST MISE EN COMMENTAIRE POUR DÉSACTIVER L'UPLOAD
    youtube_service = upload_youtube.get_authenticated_service()
    if not youtube_service:
        print("❌ Impossible d'authentifier le service YouTube. Fin du script.")
        sys.exit(1)

    # youtube_video_id = upload_youtube.upload_youtube_short(youtube_service, processed_file, youtube_metadata)

    # Remplacé par une simulation d'upload pour le débogage
    # youtube_video_id = None # Simule qu'aucun ID n'a été retourné par l'upload
    # print("⏩ Upload YouTube désactivé par le code (ligne commentée). Pas d'upload effectué.")

    if youtube_video_id: # Cette condition ne sera plus jamais vraie tant que la ligne d'upload est commentée
        print(f"🎉 Short YouTube publié avec succès ! ID: {youtube_video_id}")
        # 8. Mettre à jour l'historique des publications (ne sera pas appelé si l'upload est désactivé)
        try: # Ajout d'un try-except pour la gestion de l'historique
            add_to_history(history, selected_clip['id'], youtube_video_id)
            save_published_history(history)
            print(f"✅ Clip '{selected_clip['id']}' ajouté à l'historique des publications.")
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout/sauvegarde à l'historique après un upload (simulé ou réel): {e}")
    else:
        print("ℹ️ L'upload YouTube n'a pas été effectué ou a échoué (mode débogage).")
        # Activation de la simulation d'historique pour le débogage
        try:
            add_to_history(history, selected_clip['id'], "SIMULATED_YOUTUBE_ID")
            save_published_history(history)
            print(f"✅ Clip '{selected_clip['id']}' SIMULÉ ajouté à l'historique des publications (mode débogage).")
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout/sauvegarde SIMULÉE à l'historique : {e}")


    # 9. Nettoyage des fichiers temporaires
    print("🧹 Nettoyage des fichiers temporaires...")
    if os.path.exists(RAW_CLIP_PATH):
        os.remove(RAW_CLIP_PATH)
        print(f"  - Supprimé: {RAW_CLIP_PATH}")
    # COMMENTEZ OU SUPPRIMEZ LA LIGNE SUIVANTE POUR GARDER LE FICHIER PROCESSED_CLIP_PATH
    # if os.path.exists(PROCESSED_CLIP_PATH):
    #     os.remove(PROCESSED_CLIP_PATH)
    #     print(f"  - Supprimé: {PROCESSED_CLIP_PATH}")

    print("✅ Workflow terminé.")

if __name__ == "__main__":
    main()
    print("DEBUG: Le script main.py s'est terminé sans erreur Python.") # Ligne de débogage finale