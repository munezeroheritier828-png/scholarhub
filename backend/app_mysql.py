"""
Scholar Hub backend API — MySQL edition.

Identical API surface to app.py (the SQLite version), but reads and writes
a MySQL/MariaDB database instead. Use this if you want the app running
against a real MySQL server rather than the bundled SQLite file.

Connection settings come from environment variables, matching
build_db_mysql.py:
    MYSQL_HOST       default: 127.0.0.1
    MYSQL_PORT       default: 3306
    MYSQL_USER       default: root
    MYSQL_PASSWORD   default: '' (empty)
    MYSQL_DATABASE   default: scholarhub

Run:
    pip install -r requirements-mysql.txt
    python ../database/build_db_mysql.py   # once, to create + seed the DB
    python app_mysql.py

Serves on http://localhost:5000 (frontend included, same as app.py).
"""

import os
import secrets
from functools import wraps

import pymysql
import pymysql.cursors
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "scholarhub")

app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------------------
# Serve the frontend from the same server / same origin.
# ---------------------------------------------------------------------
@app.get("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def serve_frontend_file(filename):
    if filename.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(FRONTEND_DIR, filename)


# ---------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE, charset="utf8mb4", autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
        )
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=()):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
        last_id = cur.lastrowid
    db.commit()
    return last_id


# ---------------------------------------------------------------------
# Very small token-based auth (same scheme as the SQLite version).
# ---------------------------------------------------------------------
SESSIONS = {}  # token -> user_id


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        user_id = SESSIONS.get(token)
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        g.user_id = user_id
        return fn(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------
# Universities
# ---------------------------------------------------------------------
@app.get("/api/universities")
def list_universities():
    country = request.args.get("country")
    sql = """
        SELECT u.*, c.name AS country
        FROM universities u
        JOIN countries c ON c.country_id = u.country_id
    """
    params = []
    if country and country != "All":
        sql += " WHERE c.name = %s"
        params.append(country)
    unis = query(sql, params)

    for u in unis:
        docs = query(
            """SELECT dt.name FROM document_types dt
               JOIN university_required_documents ud ON ud.document_type_id = dt.document_type_id
               WHERE ud.university_id = %s""",
            (u["university_id"],),
        )
        u["documents"] = [d["name"] for d in docs]

        schs = query(
            """SELECT s.name FROM scholarships s
               JOIN scholarship_universities su ON su.scholarship_id = s.scholarship_id
               WHERE su.university_id = %s""",
            (u["university_id"],),
        )
        u["scholarships"] = [s["name"] for s in schs]

        u["link"] = u.pop("website")
        u["livingCost"] = u.pop("living_cost")
        u["benefits"] = u.pop("partner_benefits")
        u["partner"] = bool(u.pop("is_partner"))
        u.pop("country_id", None)

    return jsonify(unis)


# ---------------------------------------------------------------------
# Scholarships
# ---------------------------------------------------------------------
@app.get("/api/scholarships")
def list_scholarships():
    category = request.args.get("category")
    sql = "SELECT * FROM scholarships"
    params = []
    if category and category != "All":
        sql += " WHERE category = %s"
        params.append(category)
    schs = query(sql, params)

    for s in schs:
        docs = query(
            """SELECT dt.name FROM document_types dt
               JOIN scholarship_required_documents sd ON sd.document_type_id = dt.document_type_id
               WHERE sd.scholarship_id = %s""",
            (s["scholarship_id"],),
        )
        s["documents"] = [d["name"] for d in docs]

        unis = query(
            """SELECT u.name FROM universities u
               JOIN scholarship_universities su ON su.university_id = u.university_id
               WHERE su.scholarship_id = %s""",
            (s["scholarship_id"],),
        )
        s["eligibleUnis"] = [u["name"] for u in unis]

        s["link"] = s.pop("website")
        s["eligibility"] = s.pop("eligibility_notes")
        s["partner"] = bool(s.pop("is_partner"))

    return jsonify(schs)


# ---------------------------------------------------------------------
# Mentors
# ---------------------------------------------------------------------
@app.get("/api/mentors")
def list_mentors():
    mentors = query("SELECT * FROM mentors")
    for m in mentors:
        m["focus"] = m.pop("focus_area")
    return jsonify(mentors)


@app.post("/api/mentor-bookings")
@require_auth
def book_mentor():
    data = request.get_json(force=True)
    mentor_name = data.get("mentorName")
    mentor = query_one("SELECT mentor_id FROM mentors WHERE name = %s", (mentor_name,))
    if not mentor:
        return jsonify({"error": "Mentor not found"}), 404
    execute(
        "INSERT INTO mentor_bookings (mentor_id, user_id, status) VALUES (%s, %s, 'Requested')",
        (mentor["mentor_id"], g.user_id),
    )
    return jsonify({"ok": True}), 201


# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------
@app.post("/api/auth/signup")
def signup():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("name") or "").strip()
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    existing = query_one("SELECT user_id FROM users WHERE email = %s", (email,))
    if existing:
        return jsonify({"error": "An account with that email already exists"}), 409

    password_hash = generate_password_hash(password)
    user_id = execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, password_hash))
    execute("INSERT INTO student_profiles (user_id, full_name) VALUES (%s, %s)", (user_id, full_name))

    token = secrets.token_hex(24)
    SESSIONS[token] = user_id
    return jsonify({"token": token, "user": {"id": user_id, "email": email}}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = query_one("SELECT * FROM users WHERE email = %s", (email,))
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = secrets.token_hex(24)
    SESSIONS[token] = user["user_id"]
    return jsonify({"token": token, "user": {"id": user["user_id"], "email": user["email"]}})


# ---------------------------------------------------------------------
# Student profile
# ---------------------------------------------------------------------
PROFILE_FIELDS = [
    "full_name", "phone", "nationality", "district", "education_level",
    "previous_school", "grades", "key_subjects", "preferred_fields",
    "preferred_countries", "financial_need", "test_scores", "bio",
]


@app.get("/api/profile")
@require_auth
def get_profile():
    row = query_one("SELECT * FROM student_profiles WHERE user_id = %s", (g.user_id,))
    user = query_one("SELECT email FROM users WHERE user_id = %s", (g.user_id,))
    profile = dict(row) if row else {}
    if profile.get("updated_at") is not None:
        profile["updated_at"] = str(profile["updated_at"])
    profile["email"] = user["email"] if user else ""
    return jsonify(profile)


@app.put("/api/profile")
@require_auth
def update_profile():
    data = request.get_json(force=True)
    updates = {k: data.get(k, "") for k in PROFILE_FIELDS if k in data}
    if updates:
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        execute(
            f"UPDATE student_profiles SET {set_clause}, updated_at = NOW() WHERE user_id = %s",
            (*updates.values(), g.user_id),
        )
    return jsonify({"ok": True})


# ---------------------------------------------------------------------
# Document vault
# ---------------------------------------------------------------------
@app.get("/api/vault")
@require_auth
def get_vault():
    rows = query(
        """SELECT dt.name, COALESCE(vd.is_uploaded, 0) AS is_uploaded
           FROM document_types dt
           LEFT JOIN vault_documents vd ON vd.document_type_id = dt.document_type_id AND vd.user_id = %s""",
        (g.user_id,),
    )
    return jsonify([{"name": r["name"], "status": bool(r["is_uploaded"])} for r in rows])


@app.put("/api/vault")
@require_auth
def update_vault():
    data = request.get_json(force=True)
    doc_name = data.get("documentName")
    doc_type = query_one("SELECT document_type_id FROM document_types WHERE name = %s", (doc_name,))
    if not doc_type:
        return jsonify({"error": "Unknown document type"}), 404
    execute(
        """INSERT INTO vault_documents (user_id, document_type_id, is_uploaded, uploaded_at)
           VALUES (%s, %s, 1, NOW())
           ON DUPLICATE KEY UPDATE is_uploaded = 1, uploaded_at = NOW()""",
        (g.user_id, doc_type["document_type_id"]),
    )
    return jsonify({"ok": True})


# ---------------------------------------------------------------------
# Applications (tracker)
# ---------------------------------------------------------------------
@app.get("/api/applications")
@require_auth
def list_applications():
    rows = query(
        """SELECT a.application_id, a.target_type, a.status, a.created_at,
                  u.name AS university_name, s.name AS scholarship_name
           FROM applications a
           LEFT JOIN universities u ON u.university_id = a.university_id
           LEFT JOIN scholarships s ON s.scholarship_id = a.scholarship_id
           WHERE a.user_id = %s
           ORDER BY a.created_at DESC""",
        (g.user_id,),
    )
    out = []
    for r in rows:
        out.append({
            "id": r["application_id"],
            "type": r["target_type"],
            "name": r["university_name"] or r["scholarship_name"],
            "status": r["status"],
            "createdAt": str(r["created_at"]),
        })
    return jsonify(out)


@app.post("/api/applications")
@require_auth
def create_application():
    data = request.get_json(force=True)
    target_type = data.get("type")
    name = data.get("name")
    status = data.get("status", "Started")

    university_id = scholarship_id = None
    if target_type == "University":
        row = query_one("SELECT university_id FROM universities WHERE name = %s", (name,))
        university_id = row["university_id"] if row else None
    else:
        row = query_one("SELECT scholarship_id FROM scholarships WHERE name = %s", (name,))
        scholarship_id = row["scholarship_id"] if row else None

    application_id = execute(
        """INSERT INTO applications (user_id, target_type, university_id, scholarship_id, status)
           VALUES (%s, %s, %s, %s, %s)""",
        (g.user_id, target_type, university_id, scholarship_id, status),
    )
    for i, label in enumerate(["Profile complete", "Documents uploaded", "Essay drafted", "Application submitted", "Result received"]):
        execute(
            "INSERT INTO application_steps (application_id, step_order, label, state) VALUES (%s, %s, %s, 'pending')",
            (application_id, i + 1, label),
        )
    return jsonify({"id": application_id, "trackingId": f"SH-{application_id:06d}"}), 201


# ---------------------------------------------------------------------
# Payments -- metadata only. Card numbers / CVVs must NEVER be sent here.
# ---------------------------------------------------------------------
@app.post("/api/payments")
@require_auth
def create_payment():
    data = request.get_json(force=True)
    amount = data.get("amount", 10.0)
    currency = data.get("currency", "USD")
    method = data.get("method", "Card")
    application_id = data.get("applicationId")

    execute(
        """INSERT INTO payments (user_id, application_id, amount, currency, method, status)
           VALUES (%s, %s, %s, %s, %s, 'Completed')""",
        (g.user_id, application_id, amount, currency, method),
    )
    return jsonify({"ok": True}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
