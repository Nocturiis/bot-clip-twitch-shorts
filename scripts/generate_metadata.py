# scripts/generate_metadata.py
import json
from datetime import datetime
import locale
import os

def generate_youtube_metadata(clip_data):
    """
    Génère un dictionnaire de métadonnées pour un Short YouTube.

    Args:
        clip_data (dict): Le dictionnaire contenant les informations du clip sélectionné.

    Returns:
        dict: Un dictionnaire contenant 'title', 'description', et 'tags'.
    """
    print("📝 Génération des métadonnées vidéo (titre, description, tags)...")

    broadcaster_name = clip_data.get("broadcaster_name", "Un streamer")
    clip_title_raw = clip_data.get("title", "Un moment épique")
    # Nettoyer le titre du clip pour éviter des caractères non souhaités dans le titre YouTube
    clip_title_clean = clip_title_raw.replace("!", "").replace("|", "").replace(":", "").strip()

    # Tente de définir la locale pour une date en français, sinon utilise par défaut
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except locale.Error:
        try: # Essai pour macOS
            locale.setlocale(locale.LC_TIME, 'fr_FR')
        except locale.Error:
            print("⚠️ Impossible de définir la locale française pour la date. La date sera en anglais.")
            pass # Fallback to default locale if French is not available

    # Formatage de la date du jour
    today_date = datetime.now().strftime('%d %B %Y')

    # Titre du Short
    title = f"{clip_title_clean} par {broadcaster_name} | Clip Twitch du Jour FR - {today_date}"
    # S'assurer que le titre ne dépasse pas 100 caractères pour YouTube
    if len(title) > 100:
        title = title[:97] + "..." # Tronque et ajoute des points de suspension

    # Description du Short
    description = f"""Les meilleurs moments de Twitch par {broadcaster_name} !
Ce Short présente le clip le plus vu du jour : "{clip_title_raw}"

N'oubliez pas de vous abonner pour plus de Shorts Twitch chaque jour !
Chaîne de {broadcaster_name} : https://www.twitch.tv/{broadcaster_name}
Lien direct vers le clip : {clip_data.get('url', 'N/A')}

#Twitch #Shorts #ClipsTwitch #Gaming #{broadcaster_name.replace(' ', '')} #{clip_data.get('game_name', 'Gaming').replace(' ', '')}
"""
    # YouTube limite les descriptions à 5000 caractères, ce qui est largement suffisant ici.

    # Tags du Short
    tags = [
        "Twitch", "Shorts", "ClipsTwitch", "MeilleursMomentsTwitch",
        "Gaming", "Gameplay", "Drôle", "Épique", "Highlight",
        broadcaster_name, clip_data.get("game_name", "Gaming"),
        "TwitchFr", "ShortsGaming"
    ]
    # Supprimer les doublons et les tags vides/trop courts
    tags = list(set([tag.strip().replace(' ', '-') for tag in tags if tag.strip()]))
    # Assurez-vous que les tags ne dépassent pas les limites de YouTube (souvent 500 caractères au total)
    tags_string = ", ".join(tags)

    metadata = {
        "title": title,
        "description": description,
        "tags": tags_string,
        "categoryId": "20", # Catégorie "Gaming" pour YouTube
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False, # Important pour les Shorts non destinés aux enfants
        "embeddable": True,
        "license": "youtube", # Standard YouTube License
    }

    print(f"✅ Métadonnées générées.")
    print(f"  Titre: {metadata['title']}")
    # print(f"  Description (extrait): {metadata['description'][:100]}...") # Pour ne pas spammer la console
    # print(f"  Tags: {metadata['tags']}")
    
    return metadata

if __name__ == "__main__":
    # Exemple d'utilisation (pour les tests locaux)
    # Ce script est conçu pour être appelé par main.py
    print("Ce script est conçu pour être exécuté via main.py.")
    print("Pour un test direct, fournissez un dictionnaire de données de clip.")
    # Exemple de données de clip
    # test_clip_data = {
    #     "broadcaster_name": "ZeratoR",
    #     "title": "Un moment incroyable !",
    #     "game_name": "League of Legends",
    #     "url": "https://www.twitch.tv/zerator/clip/SomeTestClipID"
    # }
    # metadata = generate_youtube_metadata(test_clip_data)
    # print(json.dumps(metadata, indent=2, ensure_ascii=False))