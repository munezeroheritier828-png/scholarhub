import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scholarhub.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
c = conn.cursor()

# ---------------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------------
c.executescript("""
CREATE TABLE countries (
    country_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE
);

CREATE TABLE universities (
    university_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    country_id    INTEGER NOT NULL REFERENCES countries(country_id),
    tuition       TEXT,
    programs      TEXT,
    website       TEXT,
    is_partner    INTEGER NOT NULL DEFAULT 0 CHECK (is_partner IN (0,1)),
    deadline      TEXT,
    living_cost   TEXT,
    partner_benefits TEXT
);

CREATE TABLE scholarships (
    scholarship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL UNIQUE,
    provider       TEXT,
    category       TEXT NOT NULL CHECK (category IN ('Government','NGO','International','Local','Employer')),
    amount         TEXT,
    deadline       TEXT,
    eligibility_notes TEXT,
    website        TEXT,
    is_partner     INTEGER NOT NULL DEFAULT 0 CHECK (is_partner IN (0,1))
);

-- Many-to-many: a scholarship can work with many universities and vice versa
CREATE TABLE scholarship_universities (
    scholarship_id INTEGER NOT NULL REFERENCES scholarships(scholarship_id) ON DELETE CASCADE,
    university_id  INTEGER NOT NULL REFERENCES universities(university_id) ON DELETE CASCADE,
    PRIMARY KEY (scholarship_id, university_id)
);

CREATE TABLE document_types (
    document_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL UNIQUE
);

CREATE TABLE university_required_documents (
    university_id    INTEGER NOT NULL REFERENCES universities(university_id) ON DELETE CASCADE,
    document_type_id INTEGER NOT NULL REFERENCES document_types(document_type_id) ON DELETE CASCADE,
    PRIMARY KEY (university_id, document_type_id)
);

CREATE TABLE scholarship_required_documents (
    scholarship_id    INTEGER NOT NULL REFERENCES scholarships(scholarship_id) ON DELETE CASCADE,
    document_type_id  INTEGER NOT NULL REFERENCES document_types(document_type_id) ON DELETE CASCADE,
    PRIMARY KEY (scholarship_id, document_type_id)
);

CREATE TABLE mentors (
    mentor_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    role       TEXT,
    focus_area TEXT,
    rate       TEXT
);

CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,          -- never store plaintext passwords
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);

CREATE TABLE student_profiles (
    user_id             INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    full_name           TEXT,
    phone               TEXT,
    nationality         TEXT,
    district            TEXT,
    education_level     TEXT CHECK (education_level IN ('Senior 6 / A-Level','Undergraduate','Graduate','TVET','Other')),
    previous_school     TEXT,
    grades              TEXT,
    key_subjects        TEXT,
    preferred_fields    TEXT,
    preferred_countries TEXT,
    financial_need      TEXT CHECK (financial_need IN ('High','Medium','Low')),
    test_scores         TEXT,
    bio                 TEXT,
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE vault_documents (
    vault_document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    document_type_id  INTEGER NOT NULL REFERENCES document_types(document_type_id),
    is_uploaded       INTEGER NOT NULL DEFAULT 0 CHECK (is_uploaded IN (0,1)),
    uploaded_at       TEXT,
    UNIQUE (user_id, document_type_id)
);

CREATE TABLE applications (
    application_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    target_type      TEXT NOT NULL CHECK (target_type IN ('University','Scholarship')),
    university_id    INTEGER REFERENCES universities(university_id),
    scholarship_id   INTEGER REFERENCES scholarships(scholarship_id),
    status           TEXT NOT NULL DEFAULT 'Started' CHECK (status IN ('Started','Submitted','Under Review','Accepted','Rejected')),
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (
        (target_type='University' AND university_id IS NOT NULL AND scholarship_id IS NULL) OR
        (target_type='Scholarship' AND scholarship_id IS NOT NULL AND university_id IS NULL)
    )
);

CREATE TABLE application_steps (
    application_step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id       INTEGER NOT NULL REFERENCES applications(application_id) ON DELETE CASCADE,
    step_order            INTEGER NOT NULL,
    label                 TEXT NOT NULL,
    state                 TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','active','done')),
    completed_at          TEXT
);

CREATE TABLE mentor_bookings (
    booking_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id    INTEGER NOT NULL REFERENCES mentors(mentor_id),
    user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    status       TEXT NOT NULL DEFAULT 'Requested' CHECK (status IN ('Requested','Confirmed','Completed','Cancelled'))
);

-- Payment records only ever store non-sensitive metadata (method, amount, status).
-- Card numbers / CVVs must never be persisted here or anywhere else.
CREATE TABLE payments (
    payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    application_id  INTEGER REFERENCES applications(application_id),
    amount          NUMERIC NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    method          TEXT NOT NULL CHECK (method IN ('Card','Mobile Money')),
    status          TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Completed','Failed','Refunded')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_universities_country ON universities(country_id);
CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_vault_user ON vault_documents(user_id);
CREATE INDEX idx_payments_user ON payments(user_id);
""")

# ---------------------------------------------------------------
# SEED DATA (extracted from the project's hardcoded JS arrays)
# ---------------------------------------------------------------

countries = ["Rwanda", "Uganda", "Kenya", "Tanzania", "Burundi", "DR Congo"]
c.executemany("INSERT INTO countries (name) VALUES (?)", [(x,) for x in countries])
country_id = {name: cid for cid, name in c.execute("SELECT country_id, name FROM countries")}

universities = [
    ("University of Rwanda (UR)", "Rwanda", "≈ 600,000 – 1,200,000 RWF / yr", "Engineering, Medicine, Business, Education, Sciences", "https://www.ur.ac.rw", 1, "Rolling — intake in Sept & Jan", "≈ 150,000 – 250,000 RWF / month", "Priority review · Application fee waiver · Exclusive scholarship matching", ["Academic Transcript", "National ID / Passport"], ["SFAR", "Mastercard Foundation"]),
    ("Carnegie Mellon University Africa", "Rwanda", "Contact admissions for tuition & aid", "ICT, Electrical & Computer Engineering, Information Technology", "https://africa.engineering.cmu.edu", 1, "Jan 15 (Fall intake)", "Campus housing available — contact admissions", "Priority review · Mastercard Scholars pathway support", ["Academic Transcript", "National ID / Passport", "Recommendation Letter"], ["Mastercard Foundation"]),
    ("University of Kigali", "Rwanda", "≈ 700,000 – 1,500,000 RWF / yr", "Law, Business, IT, Public Health", "https://www.uok.ac.rw", 1, "Rolling", "≈ 180,000 – 280,000 RWF / month", "Priority review · BRD Minuza guidance · Fee waiver for eligible applicants", ["Academic Transcript", "National ID / Passport"], ["SFAR", "BRD Minuza"]),
    ("Mount Kenya University Rwanda", "Rwanda", "≈ 650,000 – 1,300,000 RWF / yr", "Business, Education, Health Sciences, Journalism", "https://mku.ac.rw", 0, "Rolling", "≈ 150,000 – 250,000 RWF / month", None, ["Academic Transcript", "National ID / Passport"], ["SFAR"]),
    ("Adventist University of Central Africa (AUCA)", "Rwanda", "≈ 600,000 – 1,100,000 RWF / yr", "Theology, Business, Nursing, Computer Science", "https://www.auca.ac.rw", 1, "Rolling", "≈ 140,000 – 220,000 RWF / month", "Priority review · BRD Minuza guidance", ["Academic Transcript", "National ID / Passport"], ["SFAR", "BRD Minuza"]),
    ("Makerere University", "Uganda", "Varies by program — see admissions", "Medicine, Engineering, Agriculture, Arts", "https://www.mak.ac.ug", 0, "See admissions calendar", "Varies — Kampala", None, ["Academic Transcript", "National ID / Passport", "Recommendation Letter"], ["DAAD", "Mastercard Foundation"]),
    ("Kyambogo University", "Uganda", "Varies by program — see admissions", "Engineering, Education, Vocational Studies", "https://kyu.ac.ug", 0, "See admissions calendar", "Varies — Kampala", None, ["Academic Transcript", "National ID / Passport"], ["DAAD"]),
    ("University of Nairobi", "Kenya", "Varies by program — see admissions", "Law, Medicine, Engineering, Business", "https://www.uonbi.ac.ke", 0, "See admissions calendar", "Varies — Nairobi", None, ["Academic Transcript", "National ID / Passport"], ["Mastercard Foundation"]),
    ("Strathmore University", "Kenya", "Varies by program — see admissions", "Business, Law, IT, Actuarial Science", "https://strathmore.edu", 0, "See admissions calendar", "Varies — Nairobi", None, ["Academic Transcript", "National ID / Passport", "Recommendation Letter"], ["Employer-Sponsored"]),
    ("University of Dar es Salaam", "Tanzania", "Varies by program — see admissions", "Engineering, Law, Social Sciences", "https://www.udsm.ac.tz", 0, "See admissions calendar", "Varies — Dar es Salaam", None, ["Academic Transcript", "National ID / Passport"], ["DAAD"]),
    ("University of Burundi", "Burundi", "Varies by program — see admissions", "Medicine, Agronomy, Law, Sciences", None, 0, "See admissions", "Varies", None, ["Academic Transcript", "National ID / Passport"], ["SFAR"]),
    ("University of Kinshasa", "DR Congo", "Varies by program — see admissions", "Medicine, Law, Engineering, Economics", None, 0, "See admissions", "Varies", None, ["Academic Transcript", "National ID / Passport"], ["DAAD"]),
]

doc_type_id = {}
def get_doc_type(name):
    if name not in doc_type_id:
        c.execute("INSERT OR IGNORE INTO document_types (name) VALUES (?)", (name,))
        c.execute("SELECT document_type_id FROM document_types WHERE name=?", (name,))
        doc_type_id[name] = c.fetchone()[0]
    return doc_type_id[name]

uni_id = {}
uni_scholarship_tags = {}  # name -> list of scholarship short-name tags (for later linking)
for (name, country, tuition, programs, link, partner, deadline, living_cost, benefits, docs, sch_tags) in universities:
    c.execute("""INSERT INTO universities (name, country_id, tuition, programs, website, is_partner, deadline, living_cost, partner_benefits)
                 VALUES (?,?,?,?,?,?,?,?,?)""",
              (name, country_id[country], tuition, programs, link, partner, deadline, living_cost, benefits))
    university_id = c.lastrowid
    uni_id[name] = university_id
    for d in docs:
        dtid = get_doc_type(d)
        c.execute("INSERT OR IGNORE INTO university_required_documents (university_id, document_type_id) VALUES (?,?)", (university_id, dtid))
    uni_scholarship_tags[name] = sch_tags

scholarships = [
    ("SFAR Student Loans", "Government of Rwanda", "Government", "Tuition + living stipend", "Rolling, annual cycle", "Any accredited Rwandan institution", "https://sfar.gov.rw", 1,
     ["Academic Transcript", "National ID / Passport"],
     ["University of Rwanda (UR)", "University of Kigali", "Adventist University of Central Africa (AUCA)", "Mount Kenya University Rwanda"]),
    ("BRD Minuza Loan Portal", "Development Bank of Rwanda", "Government", "Varies by program", "Rolling", "University of Kigali, AUCA, and partner institutions", "https://minuza.brd.rw/", 1,
     ["Academic Transcript", "National ID / Passport"],
     ["University of Kigali", "Adventist University of Central Africa (AUCA)"]),
    ("Mastercard Foundation Scholars Program", "Mastercard Foundation", "NGO", "Full tuition + stipend", "Varies by partner university", "UR, CMU-Africa, Makerere (partner institutions only)", None, 1,
     ["Academic Transcript", "National ID / Passport", "Recommendation Letter", "Personal Statement"],
     ["University of Rwanda (UR)", "Carnegie Mellon University Africa", "Makerere University"]),
    ("DAAD Scholarships — East Africa", "DAAD (Germany)", "International", "Full funding + travel", "Varies by program", "Specific graduate programs, partner universities", None, 0,
     ["Academic Transcript", "National ID / Passport", "Recommendation Letter"],
     ["Makerere University", "Kyambogo University", "University of Dar es Salaam"]),
    ("District Community Bursary", "Local district fund (example)", "Local", "Partial tuition support", "Set by district office", "Any accredited institution, district residents", None, 0,
     ["Academic Transcript", "National ID / Passport"],
     []),
    ("Twiga Capital Future Talent Award", "Twiga Capital (employer-sponsored)", "Employer", "Full tuition + guaranteed internship", "Applications open termly", "Business & IT programs, any accredited institution — includes a post-graduation internship offer", None, 0,
     ["Academic Transcript", "National ID / Passport", "Personal Statement"],
     []),
    ("Virunga Works Engineering Award", "Virunga Works (employer-sponsored)", "Employer", "Partial tuition + job placement track", "Rolling", "Engineering programs at UR, CMU-Africa, University of Kigali", None, 0,
     ["Academic Transcript", "National ID / Passport"],
     ["University of Rwanda (UR)", "Carnegie Mellon University Africa", "University of Kigali"]),
]

sch_id = {}
for (name, provider, category, amount, deadline, elig, link, partner, docs, elig_unis) in scholarships:
    c.execute("""INSERT INTO scholarships (name, provider, category, amount, deadline, eligibility_notes, website, is_partner)
                 VALUES (?,?,?,?,?,?,?,?)""", (name, provider, category, amount, deadline, elig, link, partner))
    scholarship_id = c.lastrowid
    sch_id[name] = scholarship_id
    for d in docs:
        dtid = get_doc_type(d)
        c.execute("INSERT OR IGNORE INTO scholarship_required_documents (scholarship_id, document_type_id) VALUES (?,?)", (scholarship_id, dtid))
    for uni_name in elig_unis:
        c.execute("INSERT OR IGNORE INTO scholarship_universities (scholarship_id, university_id) VALUES (?,?)", (scholarship_id, uni_id[uni_name]))

# Also link via the universities' own scholarship tag lists (short names -> full scholarship names)
tag_to_full = {
    "SFAR": "SFAR Student Loans",
    "Mastercard Foundation": "Mastercard Foundation Scholars Program",
    "BRD Minuza": "BRD Minuza Loan Portal",
    "DAAD": "DAAD Scholarships — East Africa",
    "Employer-Sponsored": None,  # generic tag, no single record
}
for uni_name, tags in uni_scholarship_tags.items():
    for t in tags:
        full = tag_to_full.get(t)
        if full and full in sch_id:
            c.execute("INSERT OR IGNORE INTO scholarship_universities (scholarship_id, university_id) VALUES (?,?)", (sch_id[full], uni_id[uni_name]))

mentors = [
    ("Aline U.", "UR Engineering Alum · Mastercard Scholar", "Essay review, interview prep", "Free · 20 min"),
    ("Eric N.", "CMU-Africa Student", "IT & Engineering applications", "Free · 20 min"),
    ("Divine K.", "AUCA Alum · SFAR recipient", "SFAR & BRD loan process walkthrough", "Free · 15 min"),
    ("Grace M.", "University of Nairobi Student", "Regional (Kenya) applications", "Free · 20 min"),
]
c.executemany("INSERT INTO mentors (name, role, focus_area, rate) VALUES (?,?,?,?)", mentors)

# Vault document types used by the app (ensure present even if no uni/scholarship referenced them)
for d in ["Academic Transcript", "National ID / Passport", "Recommendation Letter", "Personal Statement"]:
    get_doc_type(d)

conn.commit()

# ---------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------
for tbl in ["countries","universities","scholarships","scholarship_universities","document_types",
            "university_required_documents","scholarship_required_documents","mentors"]:
    n = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"{tbl}: {n} rows")

conn.close()
print("Database built at", DB_PATH)
