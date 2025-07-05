import os
import sys
from typing import List, Optional

from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ImageClip, ColorClip
from moviepy.video.fx.all import crop, even_size, resize as moviepy_resize
from skimage.filters import gaussian
import numpy as np # NOUVEL IMPORT : Ajoutez cette ligne

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


import os
import sys
from typing import List, Optional

from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ImageClip, ColorClip
from moviepy.video.fx.all import crop, even_size, resize as moviepy_resize
from skimage.filters import gaussian
import numpy as np

# ... (le code pour get_people_coords et crop_webcam reste inchangé) ...

def apply_gaussian_blur_to_frame_explicit(frame, t, sigma=15): # Fonction nommée avec 't'
    """
    Applique un flou gaussien à une image (tableau NumPy).
    Le paramètre 't' est obligatoire pour fl_image, même s'il n'est pas utilisé ici.
    """
    try:
        if not isinstance(frame, np.ndarray):
            frame = np.array(frame)

        if frame.dtype != np.float32 and frame.dtype != np.float64:
            frame = frame.astype(np.float64)

        # Utilisation de channel_axis si l'image a des canaux (RVB/RGBA)
        return gaussian(frame, sigma=sigma, channel_axis=-1 if frame.ndim == 3 else None)
    except Exception as e:
        print(f"❌ Erreur critique dans apply_gaussian_blur_to_frame_explicit: {e}")
        raise # Rélève l'exception pour que l'erreur soit visible


def trim_video_for_short(input_path, output_path, max_duration_seconds=60, clip_data=None, enable_webcam_crop=False):
    """
    Traite une vidéo pour le format Short (9:16) :
    - Coupe si elle dépasse la durée maximale.
    - Ajoute un fond flou ou recadre la webcam (si activé).
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

        found_webcam_and_cropped = False
        if enable_webcam_crop:
            cropped_webcam_clip = crop_webcam(clip)
            if cropped_webcam_clip:
                found_webcam_and_cropped = True
                main_video_clip = moviepy_resize(cropped_webcam_clip, width=target_width * 0.9)
                
                blurred_bg_clip = moviepy_resize(clip, width=target_width)
                # APPEL DE LA FONCTION NOMMÉE ICI
                blurred_bg_clip = blurred_bg_clip.fl_image(lambda frame, t: apply_gaussian_blur_to_frame_explicit(frame, t, sigma=15))
                blurred_bg_clip = blurred_bg_clip.set_position("center").set_opacity(0.8)

                all_video_elements.append(blurred_bg_clip)
                all_video_elements.append(main_video_clip.set_position(("center", "center")))
            else:
                print("La détection de webcam était activée mais n'a pas pu recadrer. Utilisation du mode fond flou.")

        if not found_webcam_and_cropped:
            bg_clip_temp = clip.copy()
            
            if bg_clip_temp.w / bg_clip_temp.h > target_width / target_height:
                blurred_bg_clip = moviepy_resize(bg_clip_temp, height=target_height)
            else:
                blurred_bg_clip = moviepy_resize(bg_clip_temp, width=target_width)

            # APPEL DE LA FONCTION NOMMÉE ICI
            blurred_bg_clip = blurred_bg_clip.fl_image(lambda frame, t: apply_gaussian_blur_to_frame_explicit(frame, t, sigma=15))
            blurred_bg_clip = blurred_bg_clip.fx(crop, width=target_width, height=target_height, x_center=blurred_bg_clip.w/2, y_center=blurred_bg_clip.h/2)
            
            main_video_clip = clip.copy()
            main_video_display_width = int(target_width * 0.9)
            main_video_clip = moviepy_resize(main_video_clip, width=main_video_display_width)
            main_video_clip = main_video_clip.fx(even_size)

            all_video_elements.append(blurred_bg_clip.set_position(("center", "center")))
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
        
        title_clip = TextClip(title_text, fontsize=40, color=text_color,
                                font=font_path, stroke_color=stroke_color, stroke_width=stroke_width,
                                size=(target_width * 0.9, None),
                                method='caption') \
                     .set_duration(duration) \
                     .set_position(("center", 50))

        streamer_clip = TextClip(f"@{streamer_name}", fontsize=30, color=text_color,
                                 font=font_path, stroke_color=stroke_color, stroke_width=stroke_width) \
                        .set_duration(duration) \
                        .set_position(("center", target_height - 100))

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