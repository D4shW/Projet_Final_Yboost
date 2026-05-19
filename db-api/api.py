"""
db-api — Service interne d'accès à la base de données.
Accessible UNIQUEMENT depuis le réseau docker interne.
"""
import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

DB_PATH = "/app/data/ants.db"
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "s3rv1c3_t0k3n_ants_lab")


def require_token():
    if request.headers.get("X-Internal-Token") != INTERNAL_TOKEN:
        abort(403)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/user")
def user():
    require_token()
    uid = request.args.get("id")
    if not uid:
        abort(400)
    conn = get_db()
    row = conn.execute(
        "SELECT id, username, role, nom, prenom, date_naissance, "
        "numero_titre, adresse, note_dossier FROM users WHERE id = ?",
        (uid,)
    ).fetchone()
    conn.close()
    if not row:
        abort(404)
    return jsonify(dict(row))


@app.route("/legacy_query", methods=["POST"])
def legacy_query():
    """
    ⚠️ Endpoint "legacy" pour compatibilité avec l'ancien portail.
    Exécute du SQL brut. Côté CTF : c'est ce qui permet la SQLi
    depuis la page de login.
    """
    require_token()
    data = request.get_json(force=True)
    sql = data.get("sql", "")
    conn = get_db()
    try:
        cur = conn.execute(sql)
        rows = [list(r) for r in cur.fetchall()]
        return jsonify({"rows": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
