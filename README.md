# 🤖 Bot de Shorts YouTube Twitch Automatisé

-----

Ce projet est un bot Python conçu pour automatiser la détection, le téléchargement, le traitement et la publication de **Shorts YouTube** à partir de clips Twitch populaires. Il est idéal pour les créateurs de contenu ou les fans souhaitant partager des moments forts de Twitch sur YouTube Shorts sans effort manuel quotidien.

Le workflow s'exécute via GitHub Actions, garantissant une automatisation complète et un déploiement simplifié.

-----

## ✨ Fonctionnalités

  * **Sélection Intelligente de Clips :** Récupère les clips les plus populaires de chaînes Twitch définies et filtre ceux déjà publiés.
  * **Téléchargement Automatisé :** Télécharge les clips Twitch sélectionnés.
  * **Traitement Vidéo Avancé (MoviePy) :**
      * **Format Vertical 9:16 :** Adapte automatiquement la vidéo au format Short (1080x1920 pixels).
      * **Découpage Intelligent :** Raccourcit les clips à une durée maximale de 60 secondes si nécessaire.
      * **Fond Personnalisé :** Remplace le fond noir générique par une image de fond personnalisée (`fond_short.png`).
      * **Rognage de Webcam (Optionnel) :** Peut tenter de détecter et de zoomer sur le visage du streamer pour une meilleure visibilité dans le Short (actuellement désactivé par défaut, nécessite une implémentation de détection de personne).
      * **Superpositions Dynamiques :** Ajoute automatiquement le titre du clip, le nom du streamer et une icône Twitch.
  * **Génération de Métadonnées SEO-Friendly :** Crée des titres, descriptions et tags optimisés pour YouTube, incluant des liens vers le clip original et la chaîne du streamer.
  * **Upload YouTube Automatisé :** Publie le Short traité directement sur une chaîne YouTube configurée.
  * **Historique des Publications :** Maintient un historique local des clips déjà publiés pour éviter les doublons.
  * **Exécution via GitHub Actions :** Le processus entier est géré par un workflow GitHub Actions, permettant une exécution programmée (ex: quotidienne) sans serveur dédié.
  * **Artefact de Sortie :** Sauvegarde toujours la vidéo Short traitée en tant qu'artefact de workflow, même si l'upload YouTube échoue.

-----

## 🚀 Démarrage Rapide

Suivez ces étapes pour configurer et exécuter le bot.

### 1\. Cloner le Dépôt

```bash
git clone https://github.com/ton_utilisateur/ton_repo.git
cd ton_repo
```

### 2\. Configuration des Secrets GitHub

Ce bot nécessite plusieurs identifiants API pour fonctionner. Ces derniers doivent être stockés en tant que **secrets de dépôt GitHub** pour des raisons de sécurité.

Allez dans `Settings` (Paramètres) de votre dépôt GitHub \> `Security` (Sécurité) \> `Secrets and variables` \> `Actions` \> `New repository secret` (Nouveau secret de dépôt).

Ajoutez les secrets suivants :

  * **`TWITCH_CLIENT_ID`** : Votre ID Client Twitch Developer.
  * **`TWITCH_CLIENT_SECRET`** : Votre Secret Client Twitch Developer.
  * **`GOOGLE_CLIENT_SECRET_JSON`** : Le **contenu complet** de votre fichier `client_secret.json` téléchargé depuis la Google Cloud Console (pour l'API YouTube). Collez le JSON entier dans la valeur du secret.
      * *Obtention :* Allez sur [Google Cloud Console](https://console.cloud.google.com/) \> `API & Services` \> `Credentials` \> `Create Credentials` \> `OAuth client ID`. Choisissez `Desktop app` (application de bureau) et téléchargez le JSON.
  * **`YOUTUBE_API_TOKEN_JSON`** : Le **contenu complet** du fichier `token.json` généré après la première authentification YouTube.
      * *Obtention :* Exécutez le bot *une première fois en local* (voir `Authentification Locale YouTube` ci-dessous) pour générer ce fichier. Copiez son contenu et collez-le ici.
      * **Important :** Ce token peut expirer ou être révoqué. Si l'upload YouTube échoue avec des erreurs d'authentification, vous devrez peut-être régénérer ce fichier `token.json` localement et mettre à jour ce secret.

### 3\. Installation des Dépendances

Les dépendances sont installées automatiquement par le workflow GitHub Actions. Cependant, pour des tests ou une exécution locale, vous pouvez les installer manuellement :

```bash
pip install -r requirements.txt
```

Le fichier `requirements.txt` devrait contenir :

```
requests
google-auth-oauthlib
google-api-python-client
moviepy
numpy
Pillow
```

### 4\. Configuration des Chaînes Twitch (`config.json`)

Créez un fichier `config.json` à la racine de votre dépôt avec la liste des chaînes Twitch à surveiller.

Exemple de `config.json` :

```json
{
  "twitch_channels": [
    "zerator",
    "squeezie",
    "mistermv",
    "byilhann"
  ]
}
```

### 5\. Préparation de l'Image de Fond et de l'Icône Twitch

  * Placez votre image de fond personnalisée pour les Shorts (recommandé : 1080x1920 pixels) dans le dossier `assets/`.
      * Assurez-vous que son nom est `fond_short.png`.
  * Placez une icône Twitch (ex: `twitch_icon.png`) dans le dossier `assets/`.
      * Si ce fichier est manquant, une alerte s'affichera dans les logs, mais le workflow continuera.

-----

## ⚙️ Workflow GitHub Actions

Le bot est configuré pour s'exécuter via GitHub Actions. Le fichier de workflow principal est `.github/workflows/main.yml`.

### Exécution Manuelle

Pour tester, vous pouvez déclencher le workflow manuellement :

1.  Allez sur votre dépôt GitHub.
2.  Cliquez sur l'onglet `Actions`.
3.  Dans la barre latérale gauche, sélectionnez `Daily Twitch Shorts Upload`.
4.  Cliquez sur `Run workflow` (Exécuter le workflow) et confirmez.

### Exécution Planifiée

Le workflow est configuré pour s'exécuter quotidiennement (par exemple, à 00:00 UTC par défaut, vérifiez votre `main.yml` pour l'heure exacte). Vous pouvez ajuster cette fréquence dans le fichier `.github/workflows/main.yml` en modifiant la section `on:schedule:`.

### Artefacts de Workflow

Même en cas d'échec de l'upload YouTube (par exemple, quota API atteint), la vidéo traitée (`temp_processed_short.mp4`) sera disponible en tant qu'**artefact de workflow**.

Pour la télécharger :

1.  Allez sur l'onglet `Actions`.
2.  Cliquez sur une exécution de workflow réussie ou échouée.
3.  Dans la section `Summary` (Résumé), recherchez la section `Artifacts` (Artefacts) et téléchargez `processed-youtube-short`.

-----

## 🛠️ Développement et Personnalisation

### Structure du Dépôt

```
.
├── .github/
│   └── workflows/
│       └── main.yml           # Workflow GitHub Actions
├── assets/
│   ├── fond_short.png         # Votre image de fond personnalisée
│   └── twitch_icon.png        # Icône Twitch pour les superpositions
├── data/                      # Dossier pour les fichiers temporaires (clips téléchargés, historique)
│   └── published_shorts_history.json
├── scripts/
│   ├── download_clip.py       # Logique de téléchargement des clips Twitch
│   ├── get_top_clips.py       # Logique de récupération et sélection des clips Twitch
│   ├── process_video.py       # Logique de traitement vidéo (MoviePy)
│   ├── generate_metadata.py   # Logique de génération des titres/descriptions/tags YouTube
│   └── upload_youtube.py      # Logique d'authentification et d'upload YouTube
├── config.json                # Fichier de configuration pour les chaînes Twitch
├── main.py                    # Point d'entrée principal du bot
└── requirements.txt           # Dépendances Python
```

### Authentification Locale YouTube (pour `token.json`)

La première fois que vous tentez d'authentifier l'API YouTube (via `main.py` en local), Google ouvrira une page dans votre navigateur pour que vous autorisiez l'application. Vous devrez copier un code de vérification et le coller dans votre terminal. Ce processus générera le fichier `token.json` qui contient les jetons d'accès.

**Étapes :**

1.  Assurez-vous que votre `GOOGLE_CLIENT_SECRET_JSON` est un fichier nommé `client_secret.json` à la racine de votre projet pour l'exécution locale.
2.  Exécutez `main.py` : `python main.py`
3.  Suivez les instructions dans le terminal et le navigateur pour l'authentification.
4.  Une fois `token.json` généré, ouvrez-le, copiez son contenu, et collez-le dans le secret GitHub `YOUTUBE_API_TOKEN_JSON`.
5.  N'oubliez pas de **supprimer `client_secret.json` et `token.json`** de votre répertoire local après les avoir configurés dans les secrets GitHub pour éviter de les commiter accidentellement.

### Personnalisation des Scripts

  * **`config.json` :** Modifiez la liste `twitch_channels` pour ajouter ou supprimer des streamers.
  * **`scripts/process_video.py` :**
      * Ajustez `target_width`, `target_height` pour la résolution des Shorts.
      * Changez le facteur de zoom (`target_width * 0.95` pour le clip principal) pour ajuster la taille de la vidéo par rapport au fond.
      * Pour activer le rognage de la webcam, implémentez la logique de détection dans `get_people_coords` (actuellement simulée à `None`) et activez `enable_webcam_crop=True` dans l'appel à `trim_video_for_short` dans `main.py`.
      * Modifiez le nom de l'image de fond si vous utilisez un nom différent de `fond_short.png`.
  * **`scripts/generate_metadata.py` :** Personnalisez les modèles de titres, descriptions et tags pour correspondre à votre marque ou style.

-----

## ⚠️ Notes Importantes

  * **Quotas YouTube API :** L'API YouTube Data v3 a des quotas d'utilisation. Si vous effectuez de nombreux uploads ou requêtes en peu de temps, vous pourriez atteindre votre quota journalier. Les uploads échoueront alors avec une erreur de quota. Vous pouvez vérifier votre utilisation dans la [Google Cloud Console](https://www.google.com/search?q=https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas).
  * **Authentification :** Assurez-vous que vos identifiants Google OAuth 2.0 ont les scopes d'API YouTube nécessaires (`youtube.upload`).
  * **Politiques YouTube :** Assurez-vous que le contenu uploadé respecte les consignes de la communauté YouTube.
  * **Fichiers Temporaires :** Le dossier `data/` est utilisé pour stocker temporairement les clips bruts et traités. Il est automatiquement nettoyé (sauf pour l'artefact processed\_short.mp4 si configuré ainsi dans `main.py`).

-----
