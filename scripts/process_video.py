# scripts/process_video.py
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.all import crop, even_size # Retire resize et set_position de cette ligne
from moviepy.video.fx.vfx import gaussian_blur # Importation spécifique pour le flou gaussien
import os
import sys

def trim_video_for_short(input_path, output_path, max_duration_seconds=60, clip_data=None):
    """
    Coupe une vidéo pour qu'elle ne dépasse pas la durée maximale spécifiée.
    Si la vidéo est plus courte, elle n'est pas modifiée.
    Convertit la vidéo en format vertical (9:16) avec un fond flou
    et ajoute le titre du clip et le nom du streamer.

    Args:
        input_path (str): Chemin vers le fichier vidéo d'entrée.
        output_path (str): Chemin où sauvegarder le fichier vidéo traité.
        max_duration_seconds (int): Durée maximale en secondes (par défaut 60s pour YouTube Shorts).
        clip_data (dict): Dictionnaire contenant les données du clip (titre, streamer, etc.).
                          Attendu: 'title', 'broadcaster_name'.

    Returns:
        str: Le chemin du fichier vidéo traité, ou None en cas d'erreur.
    """
    print(f"✂️ Traitement vidéo : {input_path}")
    print(f"Durée maximale souhaitée : {max_duration_seconds} secondes.")
    if clip_data:
        print(f"Titre du clip : {clip_data.get('title', 'N/A')}")
        print(f"Streamer : {clip_data.get('broadcaster_name', 'N/A')}")

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


        # --- Définir la résolution cible pour les Shorts (9:16) ---
        target_width, target_height = 1080, 1920 
        
        # --- Créer le clip de fond flou ---
        # 1. Redimensionner le clip original pour qu'il remplisse complètement la zone 1080x1920.
        #    Nous redimensionnons en fonction du côté le plus petit pour nous assurer de "remplir" l'écran,
        #    puis nous recadrons l'excédent.
        bg_clip_temp = clip.copy()

        target_aspect_ratio = target_width / target_height
        clip_aspect_ratio = bg_clip_temp.w / bg_clip_temp.h

        if clip_aspect_ratio < target_aspect_ratio:
            # L'original est plus "vertical" que la cible, on l'agrandit pour que sa largeur corresponde à target_width
            bg_clip_temp = bg_clip_temp.resize(width=target_width)
        else:
            # L'original est plus "horizontal" ou de même ratio, on l'agrandit pour que sa hauteur corresponde à target_height
            bg_clip_temp = bg_clip_temp.resize(height=target_height)

        # 2. Recadrer le clip agrandi au format cible (1080x1920) et le centrer
        blurred_bg_clip = bg_clip_temp.fx(crop, width=target_width, height=target_height, x_center=bg_clip_temp.w/2, y_center=bg_clip_temp.h/2)
        
        # 3. Appliquer un flou gaussien intense
        blurred_bg_clip = blurred_bg_clip.fx(gaussian_blur, sigma=15) # sigma=15 donne un bon flou

        # --- Créer le clip principal (foreground) ---
        main_clip = clip.copy()
        
        # Redimensionner le clip principal pour qu'il occupe 90% de la largeur cible (1080px).
        # Cela permet une légère marge pour l'effet de fond flou et le texte.
        main_video_display_width = int(target_width * 0.9) # Ex: 90% de 1080 = 972px
        main_clip = main_clip.resize(width=main_video_display_width)

        # Assurez-vous que les dimensions du main_clip sont paires pour MoviePy
        main_clip = main_clip.fx(even_size)
        
        # --- Compositer les clips (fond flou + vidéo principale) ---
        # Positionner le clip principal au centre du canvas total (1080x1920)
        video_with_blurred_bg = CompositeVideoClip([
            blurred_bg_clip.set_position(("center", "center")), # Le fond remplit tout l'écran
            main_clip.set_position(("center", "center")) # La vidéo principale est centrée
        ], size=(target_width, target_height)) # Définir la taille finale de la composition


        # --- Ajouter les textes (titre et nom du streamer) ---
        title_text = clip_data.get('title', 'Titre du clip')
        streamer_name = clip_data.get('broadcaster_name', 'Nom du streamer')

        # Style de texte
        font_path = "DejaVuSans-Bold" # Un exemple de police, assurez-vous qu'elle est disponible ou remplacez
        try: # Teste si la police existe via Pillow (utilisée par MoviePy)
            from PIL import ImageFont
            ImageFont.truetype(font_path, 10)
        except Exception:
            print(f"⚠️ Police '{font_path}' non trouvée ou non valide. Utilisation de la police par défaut de MoviePy.")
            font_path = "sans" # Fallback to MoviePy default

        text_color = "white"
        stroke_color = "black"
        stroke_width = 1.5
        
        # Positionnement des textes : au-dessus du clip principal, dans la zone floue supérieure
        # Calculez le haut de la vidéo principale centrée
        y_main_video_top = (video_with_blurred_bg.h - main_clip.h) / 2
        
        # Titre du clip
        title_clip = TextClip(title_text, fontsize=40, color=text_color,
                              font=font_path, stroke_color=stroke_color, stroke_width=stroke_width,
                              size=(target_width * 0.9, None), # Limite la largeur pour le wrap text
                              method='caption') \
                     .set_duration(video_with_blurred_bg.duration) \
                     .set_position(("center", y_main_video_top - TextClip("A", fontsize=40, font=font_path).h - 20)) # 20px au-dessus

        # Nom du streamer
        streamer_clip = TextClip(f"@{streamer_name}", fontsize=30, color=text_color,
                                 font=font_path, stroke_color=stroke_color, stroke_width=stroke_width) \
                        .set_duration(video_with_blurred_bg.duration) \
                        .set_position(("center", title_clip.pos[1] + title_clip.h + 10)) # 10px en dessous du titre

        # Compositer toutes les couches (vidéo + textes)
        final_video = CompositeVideoClip([video_with_blurred_bg, title_clip, streamer_clip])

        # --- Écriture du fichier final ---
        final_video.write_videofile(output_path, 
                                     codec="libx264", 
                                     audio_codec="aac", 
                                     temp_audiofile='temp-audio.m4a', 
                                     remove_temp=True,
                                     fps=clip.fps, # Maintenir le FPS original
                                     logger=None) # Supprimer les logs excessifs de moviepy
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
        if 'video_with_blurred_bg' in locals() and video_with_blurred_bg is not None:
            video_with_blurred_bg.close() # Libère les ressources de la composition intermédiaire
        if 'final_video' in locals() and final_video is not None:
            final_video.close() # Libère les ressources du clip final