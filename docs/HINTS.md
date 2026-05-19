# Indices progressifs — ANTS-Lab

> À distribuer aux joueurs selon les coûts de points que tu fixes (par ex. -10pts par hint).

## 🎯 Objectif

Vous devez exfiltrer l'intégralité de la base de données usagers (100 dossiers).

## 🔍 Étape 1 — Connexion

**Hint 1** (léger) : L'authentification semble se faire via une base de données. Que se passe-t-il si tu mets des caractères "spéciaux" dans les champs ?

**Hint 2** (moyen) : Les guillemets simples sont tes amis. Et les commentaires SQL aussi.

**Hint 3** (gros) : Essaye `admin' --` comme identifiant.

## 🔢 Étape 2 — Page dossier

**Hint 1** : Regarde l'URL après connexion. Que se passe-t-il si tu changes le paramètre ?

**Hint 2** : Tu vas vite te heurter à un mur — lis bien le message d'erreur quand ça arrive.

**Hint 3** : Le footer du dossier et la page d'erreur 429 te donnent des infos sur QUI peut bypass le rate limit. Et non, spoofer `X-Forwarded-For` ne suffit pas — Flask voit la vraie IP TCP.

## 📂 Étape 3 — Import

**Hint 1** : La fonctionnalité d'import accepte des fichiers YAML. Le YAML peut faire plus que stocker des données.

**Hint 2** : Cherche "PyYAML RCE" ou "yaml.load unsafe".

**Hint 3** : Le tag magique commence par `!!python/object/apply`.

## 🔄 Étape 4 — Pivot et dump

**Hint 1** : Tu as RCE — mais l'objectif est d'extraire les 100 dossiers. Souviens-toi de ce que tu pouvais PRESQUE faire à l'étape 2.

**Hint 2** : Depuis l'intérieur du conteneur, comment requêter le service web ? Et avec quelle IP source ?

**Hint 3** : `curl http://127.0.0.1:5000/dossier?user_id=X` avec ton cookie de session (récupérable via DevTools → Stockage → Cookies, car le cookie est HttpOnly).

**Hint 4** (expert) : Le conteneur web a peut-être des choses intéressantes dans ses variables d'environnement. Et le service de base de données interne ?
