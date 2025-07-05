# scripts/process_video.py
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.all import crop, even_size # Gardez crop et even_size ici
# Supprimez la ligne : from moviepy.video.fx.vfx import gaussian_blur

# >>> NOUVELLE IMPORTATION POUR LE FLOU GAUSSIEN <<<
from skimage.filters import gaussian
# >>> FIN NOUVELLE IMPORTATION <<<

import os
import sys

# >>> NOUVELLE FONCTION POUR APPLIQUER LE FLOU À UNE IMAGE <<<
def apply_gaussian_blur_to_frame(frame, sigma=15):
    """Applique un flou gaussien à une image (tableau NumPy)."""
    # multichannel=True est important pour les images couleur (RGB)
    return gaussian(frame, sigma=sigma, multichannel=True)
# >>> FIN NOUVELLE FONCTION <<<


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
        bg_clip_temp = clip.copy()

        target_aspect_ratio = target_width / target_height
        clip_aspect_ratio = bg_clip_temp.w / bg_clip_temp.h

        if clip_aspect_ratio < target_aspect_ratio:
            bg_clip_temp = bg_clip_temp.resize(width=target_width)
        else:
            bg_clip_temp = bg_clip_temp.resize(height=target_height)

        blurred_bg_clip = bg_clip_temp.fx(crop, width=target_width, height=target_height, x_center=bg_clip_temp.w/2, y_center=bg_clip_temp.h/2)
        
        # >>> MODIFICATION ICI : UTILISATION DE FL_IMAGE AVEC SCALING <<<
        # Appliquer un flou gaussien intense via scikit-image
        # La fonction fl_image applique une fonction à chaque image du clip.
        blurred_bg_clip = blurred_bg_clip.fl_image(lambda frame: apply_gaussian_blur_to_frame(frame, sigma=15))
        # >>> FIN MODIFICATION <<<

        # --- Créer le clip principal (foreground) ---
        main_clip = clip.copy()
        
        main_video_display_width = int(target_width * 0.9)
        main_clip = main_clip.resize(width=main_video_display_width)

        main_clip = main_clip.fx(even_size)
        
        # --- Compositer les clips (fond flou + vidéo principale) ---
        video_with_blurred_bg = CompositeVideoClip([
            blurred_bg_clip.set_position(("center", "center")),
            main_clip.set_position(("center", "center"))
        ], size=(target_width, target_height))


        # --- Ajouter les textes (titre et nom du streamer) ---
        title_text = clip_data.get('title', 'Titre du clip')
        streamer_name = clip_data.get('broadcaster_name', 'Nom du streamer')

        font_path = "DejaVuSans-Bold"
        try:
            from PIL import ImageFont
            ImageFont.truetype(font_path, 10)
        except Exception:
            print(f"⚠️ Police '{font_path}' non trouvée ou non valide. Utilisation de la police par défaut de MoviePy.")
            font_path = "sans"

        text_color = "white"
        stroke_color = "black"
        stroke_width = 1.5
        
        y_main_video_top = (video_with_blurred_bg.h - main_clip.h) / 2
        
        title_clip = TextClip(title_text, fontsize=40, color=text_color,
                              font=font_path, stroke_color=stroke_color, stroke_width=stroke_width,
                              size=(target_width * 0.9, None),
                              method='caption') \
                     .set_duration(video_with_blurred_bg.duration) \
                     .set_position(("center", y_main_video_top - TextClip("A", fontsize=40, font=font_path).h - 20))
        
        streamer_clip = TextClip(f"@{streamer_name}", fontsize=30, color=text_color,
                                 font=font_path, stroke_color=stroke_color, stroke_width=stroke_width) \
                        .set_duration(video_with_blurred_bg.duration) \
                        .set_position(("center", title_clip.pos[1] + title_clip.h + 10))

        final_video = CompositeVideoClip([video_with_blurred_bg, title_clip, streamer_clip])

        # --- Écriture du fichier final ---
        final_video.write_videofile(output_path, 
                                     codec="libx264", 
                                     audio_codec="aac", 
                                     temp_audiofile='temp-audio.m4a', 
                                     remove_temp=True,
                                     fps=clip.fps,
                                     logger=None)
        print(f"✅ Clip traité et sauvegardé : {output_path}")
        return output_path
            
    except Exception as e:
        print(f"❌ Erreur lors du traitement vidéo : {e}")
        print("Assurez-vous que 'ffmpeg' est installé et accessible dans votre PATH.")
        print("Pour l'installer: https://ffmpeg.org/download.html")
        return None
    finally:
        if 'clip' in locals() and clip is not None:
            clip.close()
        if 'video_with_blurred_bg' in locals() and video_with_blurred_bg is not None:
            video_with_blurred_bg.close()
        if 'final_video' in locals() and final_video is not None:
            final_video.close()