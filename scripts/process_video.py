import os
import sys
from typing import List, Optional

from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ImageClip, ColorClip
from moviepy.video.fx.all import crop, even_size, resize as moviepy_resize
import numpy as np # Gardé car il pourrait être utile pour d'autres traitements futurs

# ==============================================================================
# ATTENTION : Vous DEVEZ implémenter cette fonction ou la remplacer par une logique
# de détection de personne si vous voulez utiliser le rognage de webcam.
# Pour l'instant, elle retourne toujours None, désactivant le rognage de webcam.
# Si vous n'avez pas le code de 'get_people_coords', vous pouvez laisser _crop_webcam=False
# dans l'appel de trim_video_for_short dans main.py.
# ==============================================================================
def get_people_coords(image_path: str) -> Optional[List[int]]:
    """
    Simule la détection de personnes.
    Dans un vrai projet, cela ferait appel à une bibliothèque de détection de visages/corps.
    Exemple de retour : [x, y, x1, y1] des coordonnées du cadre de la personne.
    """
    # print(f"DEBUG: Tentative de détection de personne sur {image_path}")
    # Simuler l'absence de détection pour l'instant
    return None

def crop_webcam(clip: VideoFileClip) -> Optional[VideoFileClip]:
    """
    Tente de recadrer le clip autour de la zone de la webcam (visage du diffuseur).
    """
    margin_value = 20
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.abspath(os.path.join(script_dir, '..', 'data')) # Utilisez votre répertoire 'data'
    frame_image = os.path.join(temp_dir, 'webcam_search_frame.png')

    print("🔎 Recherche de la zone de la webcam (visage du diffuseur)...")
    try:
        # Assurez-vous que le répertoire existe avant d'enregistrer l'image
        os.makedirs(temp_dir, exist_ok=True)
        clip.save_frame(frame_image, t=1) # Sauvegarde une image pour analyse
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de l'image pour détection de webcam : {e}")
        return None

    box = get_people_coords(frame_image)
    if not box:
        print("\t⏩ Aucun visage de diffuseur trouvé - rognage de la webcam ignoré.")
        return None
    print("\t✅ Visage du diffuseur trouvé - rognage et zoom.")

    x, y, x1, y1 = tuple(box)
    x -= margin_value
    y -= margin_value
    x1 += margin_value
    y1 += margin_value

    # Ajustement des limites pour ne pas sortir de l'image
    x = max(0, x)
    y = max(0, y)
    x1 = min(clip.w, x1)
    y1 = min(clip.h, y1)

    # Nettoyage
    if os.path.exists(frame_image):
        os.remove(frame_image)

    return crop(clip, x1=x1, y1=y1, x2=x, y2=y)


def trim_video_for_short(input_path, output_path, max_duration_seconds=60, clip_data=None, enable_webcam_crop=False):
    """
    Traite une vidéo pour le format Short (9:16) :
    - Coupe si elle dépasse la durée maximale.
    - Ajoute un fond personnalisé (ou noir si l'image n'est pas trouvée).
    - Ajoute le titre du clip, le nom du streamer et une icône Twitch.
    """
    print(f"✂️ Traitement vidéo : {input_path}")
    print(f"Durée maximale souhaitée : {max_duration_seconds} secondes.")
    if clip_data:
        print(f"Titre du clip : {clip_data.get('title', 'N/A')}")
        print(f"Streamer : {clip_data.get('broadcaster_name', 'N/A')}")

    if not os.path.exists(input_path):
        print(f"❌ Erreur : Le fichier d'entrée n'existe pas à {input_path}")
        return None

    clip = None # Initialiser clip à None pour le finally
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

        duration = clip.duration

        # --- Définir la résolution cible pour les Shorts (9:16) ---
        target_width, target_height = 1080, 1920

        all_video_elements = [] # Liste pour tous les éléments vidéo à composer

        # --- Configuration du fond personnalisé ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.abspath(os.path.join(script_dir, '..', 'assets'))
        custom_background_image_path = os.path.join(assets_dir, 'fond_short.png') # <-- Ton fichier d'image !

        background_clip = None # Initialisation

        if not os.path.exists(custom_background_image_path):
            print(f"❌ Erreur : L'image de fond personnalisée '{os.path.basename(custom_background_image_path)}' est introuvable dans '{assets_dir}'.")
            print("Utilisation d'un fond noir par défaut.")
            background_clip = ColorClip(size=(target_width, target_height), color=(0,0,0)).set_duration(duration)
        else:
            print(f"✅ Création d'un fond personnalisé avec l'image : {os.path.basename(custom_background_image_path)}")
            try:
                background_clip = ImageClip(custom_background_image_path)
                # Redimensionne l'image pour qu'elle corresponde exactement à la résolution cible
                background_clip = background_clip.resize(newsize=(target_width, target_height))
                # Définit la durée de l'image de fond pour qu'elle dure toute la vidéo
                background_clip = background_clip.set_duration(duration)
            except Exception as e:
                print(f"❌ Erreur lors du chargement ou du traitement de l'image de fond : {e}")
                print("Utilisation d'un fond noir par défaut.")
                background_clip = ColorClip(size=(target_width, target_height), color=(0,0,0)).set_duration(duration)
        # --- Fin de la configuration du fond personnalisé ---


        found_webcam_and_cropped = False
        if enable_webcam_crop:
            cropped_webcam_clip = crop_webcam(clip)
            if cropped_webcam_clip:
                found_webcam_and_cropped = True
                main_video_clip = moviepy_resize(cropped_webcam_clip, width=target_width * 1.4) # Facteur de zoom 1.4
                
                all_video_elements.append(background_clip)
                all_video_elements.append(main_video_clip.set_position(("center", "center")))
            else:
                print("La détection de webcam était activée mais n'a pas pu recadrer. Utilisation du mode fond personnalisé.")

        if not found_webcam_and_cropped:
            all_video_elements.append(background_clip.set_position(("center", "center")))
            main_video_clip = clip.copy()
            main_video_display_width = int(target_width * 1.4) # Facteur de zoom 1.4
            main_video_clip = moviepy_resize(main_video_clip, width=main_video_display_width)
            main_video_clip = main_video_clip.fx(even_size)

            all_video_elements.append(main_video_clip.set_position(("center", "center")))
        
        video_with_visuals = CompositeVideoClip(all_video_elements, size=(target_width, target_height)).set_duration(duration)

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
        
        title_clip = TextClip(title_text, fontsize=100, color=text_color,
                                font=font_path, stroke_color=stroke_color, stroke_width=stroke_width,
                                size=(target_width * 0.9, None),
                                method='caption') \
                     .set_duration(duration) \
                     .set_position(("center", 30))

        streamer_clip = TextClip(f"@{streamer_name}", fontsize=90, color=text_color,
                                 font=font_path, stroke_color=stroke_color, stroke_width=stroke_width) \
                        .set_duration(duration) \
                        .set_position(("center", target_height - 70))

        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.abspath(os.path.join(script_dir, '..', 'assets'))
        twitch_icon_path = os.path.join(assets_dir, 'twitch_icon.png')

        twitch_icon_clip = None
        if os.path.exists(twitch_icon_path):
            try:
                twitch_icon_clip = ImageClip(twitch_icon_path, duration=duration)
                twitch_icon_clip = moviepy_resize(twitch_icon_clip, width=80)
                twitch_icon_clip = twitch_icon_clip.set_position((title_clip.pos[0] - twitch_icon_clip.w - 10, title_clip.pos[1] + 5))
                print("✅ Icône Twitch ajoutée.")
            except Exception as e:
                print(f"⚠️ Erreur lors de l'ajout de l'icône Twitch : {e}. L'icône ne sera pas ajoutée.")
                twitch_icon_clip = None
        else:
            print("⚠️ Fichier 'twitch_icon.png' non trouvé dans le dossier 'assets'. L'icône ne sera pas ajoutée.")

        final_elements = [video_with_visuals, title_clip, streamer_clip]
        if twitch_icon_clip:
            final_elements.append(twitch_icon_clip)

        final_video = CompositeVideoClip(final_elements)

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
        if 'video_with_visuals' in locals() and video_with_visuals is not None:
            video_with_visuals.close()
        if 'final_video' in locals() and final_video is not None:
            final_video.close()