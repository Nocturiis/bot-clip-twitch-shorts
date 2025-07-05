# scripts/process_video.py
from moviepy.editor import VideoFileClip
import os
import sys

def trim_video_for_short(input_path, output_path, max_duration_seconds=60):
    """
    Coupe une vidéo pour qu'elle ne dépasse pas la durée maximale spécifiée.
    Si la vidéo est plus courte, elle n'est pas modifiée.
    Convertit également la vidéo en format vertical (9:16) si nécessaire.

    Args:
        input_path (str): Chemin vers le fichier vidéo d'entrée.
        output_path (str): Chemin où sauvegarder le fichier vidéo traité.
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
        
        original_width, original_height = clip.size
        print(f"Résolution originale du clip : {original_width}x{original_height}")

        # --- Gérer la durée ---
        if clip.duration > max_duration_seconds:
            print(f"Le clip ({clip.duration:.2f}s) dépasse la durée maximale. Découpage à {max_duration_seconds}s.")
            clip = clip.subclip(0, max_duration_seconds)
        else:
            print(f"Le clip ({clip.duration:.2f}s) est déjà dans la limite de durée.")

        # --- Gérer le format vertical (9:16, ex: 1080x1920) ---
        target_aspect_ratio = 9 / 16 # Vertical (largeur / hauteur)
        
        current_aspect_ratio = clip.w / clip.h

        # Si la vidéo est plus large que 9:16 (horizontale, carrée, ou moins verticale)
        if current_aspect_ratio > target_aspect_ratio: 
            print("Conversion vers un format vertical (9:16) requise. Redimensionnement et recadrage...")
            
            # Définir la hauteur cible pour la qualité (ex: 1920 pour Full HD vertical)
            target_height = 1920 
            # Calculer la largeur correspondante pour un ratio 9:16
            target_width = int(target_height * target_aspect_ratio) # Sera 1080 si target_height est 1920

            # 1. Redimensionner le clip pour que sa hauteur corresponde à la hauteur cible
            # Cela va potentiellement rendre le clip plus large que target_width si l'original est très large
            scaled_clip = clip.resize(height=target_height)
            
            # 2. Recadrer le clip horizontalement pour obtenir la largeur cible (centré)
            x_center_scaled = scaled_clip.w / 2
            x1_scaled = max(0, int(x_center_scaled - target_width / 2))
            x2_scaled = min(scaled_clip.w, int(x_center_scaled + target_width / 2))
            
            clip = scaled_clip.crop(x1=x1_scaled, y1=0, x2=x2_scaled, y2=target_height)
            print(f"Redimensionné et recadré à {clip.w}x{clip.h} (format 9:16)")

        # Si la vidéo est déjà plus verticale que 9:16 (ex: 1:2)
        elif current_aspect_ratio < target_aspect_ratio: 
            print("Le clip est déjà en format vertical ou plus étroit que 9:16. Redimensionnement pour qualité si nécessaire.")
            # Assurez une hauteur minimale pour une bonne qualité (ex: 720p)
            if clip.h < 720: 
                clip = clip.resize(height=720)
                print(f"Redimensionné pour une hauteur minimale de 720p: {clip.w}x{clip.h}")
            else:
                print(f"Le clip est déjà en format vertical suffisant: {clip.w}x{clip.h}.")

        else: # Si la vidéo est déjà exactement 9:16
            print("Le clip est déjà en format 9:16.")


        # --- Écriture du fichier final ---
        clip.write_videofile(output_path, 
                             codec="libx264", 
                             audio_codec="aac", 
                             temp_audiofile='temp-audio.m4a', 
                             remove_temp=True,
                             logger=None) # Ajoutez logger=None pour réduire les logs de moviepy
        print(f"✅ Clip traité et sauvegardé : {output_path}")
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
    #       print(f"Test processing complete: {processed_file}")