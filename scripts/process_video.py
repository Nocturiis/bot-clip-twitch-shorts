# scripts/process_video.py
from moviepy.editor import VideoFileClip
import os
import sys

def trim_video_for_short(input_path, output_path, max_duration_seconds=60):
    """
    Coupe une vidéo pour qu'elle ne dépasse pas la durée maximale spécifiée.
    Si la vidéo est plus courte, elle n'est pas modifiée.

    Args:
        input_path (str): Chemin vers le fichier vidéo d'entrée.
        output_path (str): Chemin où sauvegarder le fichier vidéo coupé.
        max_duration_seconds (int): Durée maximale en secondes (par défaut 60s pour YouTube Shorts).

    Returns:
        str: Le chemin du fichier vidéo traité, ou None en cas d'erreur.
    """
    print(f"✂️ Traitement vidéo : {input_path}")
    print(f"Durée maximale souhaitée : {max_duration_seconds} secondes.")

    if not os.path.exists(input_path):
        print(f"❌ Erreur : Le fichier d'entrée n'existe pas à {input_path}")
        return None

    try:
        clip = VideoFileClip(input_path)
        
        if clip.duration > max_duration_seconds:
            print(f"Le clip ({clip.duration:.2f}s) dépasse la durée maximale. Découpage à {max_duration_seconds}s.")
            trimmed_clip = clip.subclip(0, max_duration_seconds)
            trimmed_clip.write_videofile(output_path, 
                                         codec="libx264", 
                                         audio_codec="aac", 
                                         temp_audiofile='temp-audio.m4a', 
                                         remove_temp=True)
            print(f"✅ Clip découpé et sauvegardé : {output_path}")
            return output_path
        else:
            print(f"Le clip ({clip.duration:.2f}s) est déjà dans la limite. Copie vers {output_path}.")
            # Si le clip est déjà assez court, on le copie simplement
            # shutil.copy(input_path, output_path) # moviepy write_videofile est plus sûr pour le format
            clip.write_videofile(output_path, 
                                 codec="libx264", 
                                 audio_codec="aac", 
                                 temp_audiofile='temp-audio.m4a', 
                                 remove_temp=True)
            print(f"✅ Clip copié : {output_path}")
            return output_path
            
    except Exception as e:
        print(f"❌ Erreur lors du traitement vidéo : {e}")
        print("Assurez-vous que 'ffmpeg' est installé et accessible dans votre PATH.")
        print("Pour l'installer: https://ffmpeg.org/download.html")
        return None
    finally:
        if 'clip' in locals() and clip is not None:
            clip.close() # Libère les ressources du clip moviepy

if __name__ == "__main__":
    # Exemple d'utilisation (pour les tests locaux)
    # Ce script est conçu pour être appelé par main.py
    print("Ce script est conçu pour être exécuté via main.py.")
    print("Il nécessite 'ffmpeg' et 'moviepy' (pip install moviepy).")
    # Pour tester, vous auriez besoin d'un fichier vidéo existant
    # input_file_test = os.path.join("data", "downloaded_clip_test.mp4")
    # output_file_test = os.path.join("data", "processed_clip_test.mp4")
    # processed_file = trim_video_for_short(input_file_test, output_file_test)
    # if processed_file:
    #     print(f"Test processing complete: {processed_file}")