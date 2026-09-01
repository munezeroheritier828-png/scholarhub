"""
Scholar Hub backend API.

A small Flask REST API that sits on top of the SQLite database in
../database/scholarhub.db and serves everything the frontend needs:
universities, scholarships, mentors, auth, student profile, the
document vault, the application tracker, mentor bookings, and payment
records (metadata only -- card numbers are never accepted or stored
here or anywhere else).

Run:
    pip install -r requirements.txt
    python app.py

Serves on http://localhost:5000
"""

import os
import sqlite3
import secrets
from functools import wraps

from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "scholarhub.db")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__)
CORS(app)  # harmless once same-origin, useful if you ever split the deployment


# ---------------------------------------------------------------------
# Serve the frontend from the same server, same origin, no path guessing.
# This is what fixes "the page loads with no styling": opening index.html
# by double-clicking it (file://) can silently fail to load style.css
# depending on the browser/OS. Loading everything through Flask avoids
# that entirely — one command, one origin, works the same everywhere.
# ---------------------------------------------------------------------
@app.get("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def serve_frontend_file(filename):
    # Never let this shadow the /api/* routes below.
    if filename.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(FRONTEND_DIR, filename)



# ---------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def rows_to_list(rows):
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# Very small token-based auth.
# A token is just a random string stored in the in-memory SESSIONS map
# alongside the user_id. Good enough for a prototype; swap for signed
# JWTs or server-side sessions before shipping to production.
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
    db = get_db()
    country = request.args.get("country")
    query = """
        SELECT u.*, c.name AS country
        FROM universities u
        JOIN countries c ON c.country_id = u.country_id
    """
    params = []
    if country and country != "All":
        query += " WHERE c.name = ?"
        params.append(country)
    unis = rows_to_list(db.execute(query, params).fetchall())

    for u in unis:
        docs = db.execute(
            """SELECT dt.name FROM document_types dt
               JOIN university_required_documents ud ON ud.document_type_id = dt.document_type_id
               WHERE ud.university_id = ?""",
            (u["university_id"],),
        ).fetchall()
        u["documents"] = [d["name"] for d in docs]

        schs = db.execute(
            """SELECT s.name FROM scholarships s
               JOIN scholarship_universities su ON su.scholarship_id = s.scholarship_id
               WHERE su.university_id = ?""",
            (u["university_id"],),
        ).fetchall()
        u["scholarships"] = [s["name"] for s in schs]

        u["link"] = u.pop("website")
        u["tuition"] = u["tuition"]
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
    db = get_db()
    category = request.args.get("category")
    query = "SELECT * FROM scholarships"
    params = []
    if category and category != "All":
        query += " WHERE category = ?"
        params.append(category)
    schs = rows_to_list(db.execute(query, params).fetchall())

    for s in schs:
        docs = db.execute(
            """SELECT dt.name FROM document_types dt
               JOIN scholarship_required_documents sd ON sd.document_type_id = dt.document_type_id
               WHERE sd.scholarship_id = ?""",
            (s["scholarship_id"],),
        ).fetchall()
        s["documents"] = [d["name"] for d in docs]

        unis = db.execute(
            """SELECT u.name FROM universities u
               JOIN scholarship_universities su ON su.university_id = u.university_id
               WHERE su.scholarship_id = ?""",
            (s["scholarship_id"],),
        ).fetchall()
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
    db = get_db()
    mentors = rows_to_list(db.execute("SELECT * FROM mentors").fetchall())
    for m in mentors:
        m["focus"] = m.pop("focus_area")
    return jsonify(mentors)


@app.post("/api/mentor-bookings")
@require_auth
def book_mentor():
    data = request.get_json(force=True)
    mentor_name = data.get("mentorName")
    db = get_db()
    mentor = db.execute("SELECT mentor_id FROM mentors WHERE name = ?", (mentor_name,)).fetchone()
    if not mentor:
        return jsonify({"error": "Mentor not found"}), 404
    db.execute(
        "INSERT INTO mentor_bookings (mentor_id, user_id, status) VALUES (?, ?, 'Requested')",
        (mentor["mentor_id"], g.user_id),
    )
    db.commit()
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

    db = get_db()
    existing = db.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "An account with that email already exists"}), 409

    password_hash = generate_password_hash(password)
    cur = db.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password_hash))
    user_id = cur.lastrowid
    db.execute(
        "INSERT INTO student_profiles (user_id, full_name) VALUES (?, ?)",
        (user_id, full_name),
    )
    db.commit()

    token = secrets.token_hex(24)
    SESSIONS[token] = user_id
    return jsonify({"token": token, "user": {"id": user_id, "email": email}}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
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
    db = get_db()
    row = db.execute("SELECT * FROM student_profiles WHERE user_id = ?", (g.user_id,)).fetchone()
    user = db.execute("SELECT email FROM users WHERE user_id = ?", (g.user_id,)).fetchone()
    profile = dict(row) if row else {}
    profile["email"] = user["email"] if user else ""
    return jsonify(profile)


@app.put("/api/profile")
@require_auth
def update_profile():
    data = request.get_json(force=True)
    db = get_db()
    updates = {k: data.get(k, "") for k in PROFILE_FIELDS if k in data}
    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        db.execute(
            f"UPDATE student_profiles SET {set_clause}, updated_at = datetime('now') WHERE user_id = ?",
            (*updates.values(), g.user_id),
        )
        db.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------
# Document vault
# ---------------------------------------------------------------------
@app.get("/api/vault")
@require_auth
def get_vault():
    db = get_db()
    rows = db.execute(
        """SELECT dt.name, COALESCE(vd.is_uploaded, 0) AS is_uploaded
           FROM document_types dt
           LEFT JOIN vault_documents vd ON vd.document_type_id = dt.document_type_id AND vd.user_id = ?""",
        (g.user_id,),
    ).fetchall()
    return jsonify([{"name": r["name"], "status": bool(r["is_uploaded"])} for r in rows])


@app.put("/api/vault")
@require_auth
def update_vault():
    data = request.get_json(force=True)
    doc_name = data.get("documentName")
    db = get_db()
    doc_type = db.execute("SELECT document_type_id FROM document_types WHERE name = ?", (doc_name,)).fetchone()
    if not doc_type:
        return jsonify({"error": "Unknown document type"}), 404
    db.execute(
        """INSERT INTO vault_documents (user_id, document_type_id, is_uploaded, uploaded_at)
           VALUES (?, ?, 1, datetime('now'))
           ON CONFLICT(user_id, document_type_id)
           DO UPDATE SET is_uploaded = 1, uploaded_at = datetime('now')""",
        (g.user_id, doc_type["document_type_id"]),
    )
    db.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------
# Applications (tracker)
# ---------------------------------------------------------------------
@app.get("/api/applications")
@require_auth
def list_applications():
    db = get_db()
    rows = db.execute(
        """SELECT a.application_id, a.target_type, a.status, a.created_at,
                  u.name AS university_name, s.name AS scholarship_name
           FROM applications a
           LEFT JOIN universities u ON u.university_id = a.university_id
           LEFT JOIN scholarships s ON s.scholarship_id = a.scholarship_id
           WHERE a.user_id = ?
           ORDER BY a.created_at DESC""",
        (g.user_id,),
    ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r["application_id"],
            "type": r["target_type"],
            "name": r["university_name"] or r["scholarship_name"],
            "status": r["status"],
            "createdAt": r["created_at"],
        })
    return jsonify(out)


@app.post("/api/applications")
@require_auth
def create_application():
    data = request.get_json(force=True)
    target_type = data.get("type")
    name = data.get("name")
    status = data.get("status", "Started")
    db = get_db()

    university_id = scholarship_id = None
    if target_type == "University":
        row = db.execute("SELECT university_id FROM universities WHERE name = ?", (name,)).fetchone()
        university_id = row["university_id"] if row else None
    else:
        row = db.execute("SELECT scholarship_id FROM scholarships WHERE name = ?", (name,)).fetchone()
        scholarship_id = row["scholarship_id"] if row else None

    cur = db.execute(
        """INSERT INTO applications (user_id, target_type, university_id, scholarship_id, status)
           VALUES (?, ?, ?, ?, ?)""",
        (g.user_id, target_type, university_id, scholarship_id, status),
    )
    application_id = cur.lastrowid
    for i, label in enumerate(["Profile complete", "Documents uploaded", "Essay drafted", "Application submitted", "Result received"]):
        db.execute(
            "INSERT INTO application_steps (application_id, step_order, label, state) VALUES (?, ?, ?, 'pending')",
            (application_id, i + 1, label),
        )
    db.commit()
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

    db = get_db()
    db.execute(
        """INSERT INTO payments (user_id, application_id, amount, currency, method, status)
           VALUES (?, ?, ?, ?, ?, 'Completed')""",
        (g.user_id, application_id, amount, currency, method),
    )
    db.commit()
    return jsonify({"ok": True}), 201


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        raise SystemExit(
            f"Database not found at {DB_PATH}. Run database/build_db.py first."
        )
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
