# ANTS-Lab — CTF Challenge

> Challenge CTF en chaîne d'exploitation autour d'un faux portail de titres sécurisés.
> Inspiré (de loin) par l'actualité ANTS — entièrement fictif.

## ⚠️ Disclaimer

**Environnement strictement pédagogique.** Aucun lien avec l'Agence Nationale des Titres
Sécurisés réelle. Tout est fictif : nom, design, données, vulnérabilités.

## 🎯 Objectif du challenge

**Exfiltrer l'intégralité de la base de données usagers (100 dossiers)** en exploitant
une chaîne de vulnérabilités complète sur le portail.

La validation se fait à la soumission du dump complet (JSON, CSV, capture, etc.)
selon les règles fixées par l'organisateur.

## 🔗 Chaîne d'exploitation

```
Login (SQLi) → Dossier (IDOR + Rate Limit) → Import YAML → RCE → Pivot localhost → Dump complet
```

| # | Vuln | Fichier concerné |
|---|------|------------------|
| 1 | SQL Injection (auth bypass) | `web/app.py` → route `/login` + `db-api/api.py` → `/legacy_query` |
| 2 | IDOR sur `user_id` | `web/app.py` → route `/dossier` |
| 3 | Rate limit bypassable via localhost uniquement | `web/app.py` → décorateur `rate_limit` |
| 4 | RCE via `yaml.load()` non-safe | `web/app.py` → route `/import` |
| 5 | Pivot : RCE → boucle IDOR via `curl 127.0.0.1` | logique post-exploit |

## 🚀 Déploiement

```bash
docker compose up --build
```

Accessible sur `http://localhost:8080`.

- **web** : port 8080 (exposé)
- **db-api** : port 5001 (réseau docker interne uniquement, pas accessible depuis l'hôte)

## 📊 Base de données

- **100 utilisateurs** au total (IDs 1 à 100, contigus)
- Données 100 % fictives : noms, prénoms, dates de naissance, adresses, numéros de titre, notes de dossier
- ID 1 : compte `demo` / mdp `demo123`
- ID 2 : compte `admin` (découvrable une fois SQLi exploitée)
- IDs 3-100 : utilisateurs générés aléatoirement (seed fixe = reproductible)

## 🔧 Configuration

Dans `docker-compose.yml` :
- `FLASK_SECRET` : clé de session
- `INTERNAL_TOKEN` : token entre web ↔ db-api

Pour varier les données entre instances, change `random.seed(42)` dans `db-api/init_db.py`,
puis rebuild :
```bash
docker compose down -v
docker compose up --build
```

## 📁 Structure

```
ants-lab/
├── docker-compose.yml
├── web/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py              # Application Flask vulnérable
│   ├── templates/          # Vues HTML (dark mode emerald)
│   └── uploads/            # Uploads YAML (volatile)
├── db-api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api.py              # Service interne DB
│   ├── init_db.py          # Génération des 100 utilisateurs fictifs
│   └── data/               # SQLite (volume persistant)
└── docs/
    ├── WALKTHROUGH.md      # Solution complète
    └── HINTS.md            # Indices progressifs pour les joueurs
```

## 📊 Difficulté estimée

**Intermédiaire** — chaque vuln prise individuellement est classique, mais la **chaîne**
et surtout l'idée du **pivot via localhost** demandent une vraie compréhension du modèle
de menace réseau.

Temps estimé : 1h30 à 3h pour un joueur intermédiaire.

## 🧪 Validation

Au choix de l'organisateur :
- Soumission du dump (JSON, CSV) en pièce jointe
- Capture d'écran d'un échantillon des 100 dossiers
- Validation orale lors d'une démo de l'exploit

Voir `docs/WALKTHROUGH.md` pour la solution intégrale (à ne pas distribuer aux joueurs).
