"""
ANTS-Lab — Application fictive d'entraînement CTF
Simulation pédagogique inspirée d'un portail de titres sécurisés.

⚠️ CE CODE EST VOLONTAIREMENT VULNÉRABLE — usage CTF uniquement.
"""
import os
import time
import sqlite3
import secrets
from collections import defaultdict
from functools import wraps

import requests
import yaml
from flask import (
    Flask, request, render_template, redirect, url_for,
    session, jsonify, make_response, send_from_directory, abort
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev_secret")

DB_API_URL = os.environ.get("DB_API_URL", "http://db-api:5001")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "s3rv1c3_t0k3n_ants_lab")

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
#  RATE LIMITER
# ─────────────────────────────────────────────────────────────
#
#  Design pédagogique :
#  - On lit l'IP "réelle" depuis request.remote_addr (IP TCP réelle)
#  - On checke X-Forwarded-For UNIQUEMENT pour l'affichage / logs (faux indice)
#  - La whitelist localhost s'applique sur remote_addr donc impossible
#    de la bypass juste en spoofant un header.
#  - SEUL le pivot via RCE (requête réellement émise depuis le conteneur) marche.
#
_rate_buckets = defaultdict(list)
RATE_LIMIT = 5          # 5 requêtes
RATE_WINDOW = 60        # par minute
WHITELIST = {"127.0.0.1", "::1", "localhost"}


def real_client_ip():
    """IP réelle vue par Flask (couche TCP). Ne PAS confondre avec X-Forwarded-For."""
    return request.remote_addr or "0.0.0.0"


def rate_limit(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        ip = real_client_ip()
        # Bypass localhost — c'est CE comportement que le joueur doit exploiter via RCE
        if ip in WHITELIST:
            return view(*args, **kwargs)

        now = time.time()
        bucket = _rate_buckets[ip]
        # Nettoyage des entrées expirées
        _rate_buckets[ip] = [t for t in bucket if now - t < RATE_WINDOW]
        if len(_rate_buckets[ip]) >= RATE_LIMIT:
            resp = make_response(
                render_template("rate_limited.html",
                                wait=int(RATE_WINDOW - (now - _rate_buckets[ip][0]))),
                429
            )
            return resp
        _rate_buckets[ip].append(now)
        return view(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────
#  HELPERS DB-API (passe par le réseau interne docker)
# ─────────────────────────────────────────────────────────────
def db_query(endpoint, **params):
    headers = {"X-Internal-Token": INTERNAL_TOKEN}
    r = requests.get(f"{DB_API_URL}{endpoint}", params=params, headers=headers, timeout=5)
    return r.json() if r.ok else None


def db_post(endpoint, json_data):
    headers = {"X-Internal-Token": INTERNAL_TOKEN}
    r = requests.post(f"{DB_API_URL}{endpoint}", json=json_data, headers=headers, timeout=5)
    return r.json() if r.ok else None


# ─────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ━━━━━━━━━━ ÉTAPE 1 : LOGIN avec SQL INJECTION ━━━━━━━━━━━━━━
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # ⚠️ VOLONTAIREMENT VULNÉRABLE : la db-api accepte des requêtes SQL brutes
        # via un endpoint "legacy" pour la compatibilité (haha)
        # → on construit la query côté web et on l'envoie à la db-api
        # Le joueur peut injecter : username = admin' --
        # ou: ' OR 1=1 --
        sql = f"SELECT id, username, role FROM users WHERE username='{username}' AND password='{password}'"
        result = db_post("/legacy_query", {"sql": sql})

        if result and result.get("rows"):
            user = result["rows"][0]
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[2]
            return redirect(url_for("dossier"))
        else:
            error = "Identifiants invalides"

    return render_template("login.html", error=error)


# ━━━━━━━━━━ ÉTAPE 2 : PAGE DOSSIER avec IDOR ━━━━━━━━━━━━━━━━
@app.route("/dossier")
@rate_limit
def dossier():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # IDOR : on prend user_id depuis query string si fourni, sinon depuis session
    # Aucune vérif que session["user_id"] == requested_id
    requested_id = request.args.get("user_id", session["user_id"])

    try:
        requested_id = int(requested_id)
    except (TypeError, ValueError):
        abort(400)

    data = db_query("/user", id=requested_id)
    if not data:
        abort(404)

    # Faux indice : on affiche l'IP "détectée" via X-Forwarded-For dans le footer
    # → pousse les joueurs à essayer de spoofer ce header (qui ne marche PAS pour le rate limit)
    displayed_ip = request.headers.get("X-Forwarded-For", real_client_ip())

    return render_template("dossier.html", user=data, displayed_ip=displayed_ip)


# ━━━━━━━━━━ ÉTAPE 3 : UPLOAD + ÉTAPE 4 : RCE via PyYAML ━━━━━
@app.route("/import", methods=["GET", "POST"])
def import_dossier():
    """
    Permet d'importer un dossier au format YAML
    (ex: migration depuis l'ancien système ANTS).

    ⚠️ VOLONTAIREMENT VULNÉRABLE : yaml.load() sans SafeLoader
    → permet l'exécution de code arbitraire via les tags Python.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    message = None
    parsed = None

    if request.method == "POST":
        f = request.files.get("dossier_file")
        if not f:
            message = "Aucun fichier reçu."
        else:
            # Validation "stricte" : doit finir par .yaml ou .yml
            if not (f.filename.endswith(".yaml") or f.filename.endswith(".yml")):
                message = "Format invalide. Seuls les fichiers .yaml/.yml sont acceptés."
            else:
                # On sauvegarde dans uploads/ (pour audit, hihi)
                safe_name = f"{secrets.token_hex(8)}_{os.path.basename(f.filename)}"
                save_path = os.path.join(UPLOAD_DIR, safe_name)
                f.save(save_path)

                # ⚠️ LA VULNÉRABILITÉ
                try:
                    with open(save_path, "r") as fp:
                        parsed = yaml.load(fp, Loader=yaml.Loader)  # 🔥 unsafe
                    message = "Dossier importé avec succès."
                except Exception as e:
                    message = f"Erreur lors du parsing : {e}"

    return render_template("import.html", message=message, parsed=parsed)


# ━━━━━━━━━━ Logout ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ━━━━━━━━━━ Page d'erreur ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
