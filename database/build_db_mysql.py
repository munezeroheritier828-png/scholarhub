"""
Builds the Scholar Hub schema and seed data in a MySQL (or MariaDB, which
speaks the same protocol) database. This is the MySQL counterpart to
build_db.py, which builds the same data into SQLite.

Connection settings come from environment variables, with sensible local
defaults:
    MYSQL_HOST       default: 127.0.0.1
    MYSQL_PORT       default: 3306
    MYSQL_USER       default: root
    MYSQL_PASSWORD   default: '' (empty)
    MYSQL_DATABASE   default: scholarhub

Run:
    pip install -r requirements-mysql.txt
    python build_db_mysql.py
"""

import os
import pymysql

HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
PORT = int(os.environ.get("MYSQL_PORT", "3306"))
USER = os.environ.get("MYSQL_USER", "root")
PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
DATABASE = os.environ.get("MYSQL_DATABASE", "scholarhub")

# Connect without selecting a database first, so we can create it if needed.
bootstrap = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, charset="utf8mb4")
with bootstrap.cursor() as cur:
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
bootstrap.commit()
bootstrap.close()

conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database=DATABASE, charset="utf8mb4", autocommit=False)
c = conn.cursor()

# ---------------------------------------------------------------
# SCHEMA (drop and recreate, same as build_db.py's behavior for SQLite)
# ---------------------------------------------------------------
c.execute("SET FOREIGN_KEY_CHECKS = 0;")
for tbl in ["payments", "mentor_bookings", "application_steps", "applications", "vault_documents",
            "student_profiles", "users", "mentors", "scholarship_required_documents",
            "university_required_documents", "document_types", "scholarship_universities",
            "scholarships", "universities", "countries"]:
    c.execute(f"DROP TABLE IF EXISTS `{tbl}`;")
c.execute("SET FOREIGN_KEY_CHECKS = 1;")

DDL_STATEMENTS = [
"""CREATE TABLE countries (
    country_id   INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE universities (
    university_id INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(255) NOT NULL UNIQUE,
    country_id    INT NOT NULL,
    tuition       VARCHAR(255),
    programs      TEXT,
    website       VARCHAR(255),
    is_partner    TINYINT(1) NOT NULL DEFAULT 0,
    deadline      VARCHAR(255),
    living_cost   VARCHAR(255),
    partner_benefits TEXT,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE scholarships (
    scholarship_id INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(255) NOT NULL UNIQUE,
    provider       VARCHAR(255),
    category       VARCHAR(50) NOT NULL CHECK (category IN ('Government','NGO','International','Local','Employer')),
    amount         VARCHAR(255),
    deadline       VARCHAR(255),
    eligibility_notes TEXT,
    website        VARCHAR(255),
    is_partner     TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE scholarship_universities (
    scholarship_id INT NOT NULL,
    university_id  INT NOT NULL,
    PRIMARY KEY (scholarship_id, university_id),
    FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id) ON DELETE CASCADE,
    FOREIGN KEY (university_id) REFERENCES universities(university_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE document_types (
    document_type_id INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE university_required_documents (
    university_id    INT NOT NULL,
    document_type_id INT NOT NULL,
    PRIMARY KEY (university_id, document_type_id),
    FOREIGN KEY (university_id) REFERENCES universities(university_id) ON DELETE CASCADE,
    FOREIGN KEY (document_type_id) REFERENCES document_types(document_type_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE scholarship_required_documents (
    scholarship_id    INT NOT NULL,
    document_type_id  INT NOT NULL,
    PRIMARY KEY (scholarship_id, document_type_id),
    FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id) ON DELETE CASCADE,
    FOREIGN KEY (document_type_id) REFERENCES document_types(document_type_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE mentors (
    mentor_id  INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    role       VARCHAR(255),
    focus_area VARCHAR(255),
    rate       VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active     TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE student_profiles (
    user_id             INT PRIMARY KEY,
    full_name           VARCHAR(255),
    phone               VARCHAR(50),
    nationality         VARCHAR(100),
    district            VARCHAR(100),
    education_level     VARCHAR(50) CHECK (education_level IN ('Senior 6 / A-Level','Undergraduate','Graduate','TVET','Other')),
    previous_school     VARCHAR(255),
    grades              VARCHAR(255),
    key_subjects        TEXT,
    preferred_fields    TEXT,
    preferred_countries TEXT,
    financial_need      VARCHAR(20) CHECK (financial_need IN ('High','Medium','Low')),
    test_scores         VARCHAR(255),
    bio                 TEXT,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE vault_documents (
    vault_document_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NOT NULL,
    document_type_id  INT NOT NULL,
    is_uploaded       TINYINT(1) NOT NULL DEFAULT 0,
    uploaded_at       DATETIME NULL,
    UNIQUE KEY uq_user_doc (user_id, document_type_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (document_type_id) REFERENCES document_types(document_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE applications (
    application_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    target_type      VARCHAR(20) NOT NULL CHECK (target_type IN ('University','Scholarship')),
    university_id    INT NULL,
    scholarship_id   INT NULL,
    status           VARCHAR(30) NOT NULL DEFAULT 'Started' CHECK (status IN ('Started','Submitted','Under Review','Accepted','Rejected')),
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (university_id) REFERENCES universities(university_id),
    FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id),
    CHECK (
        (target_type='University' AND university_id IS NOT NULL AND scholarship_id IS NULL) OR
        (target_type='Scholarship' AND scholarship_id IS NOT NULL AND university_id IS NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE application_steps (
    application_step_id INT AUTO_INCREMENT PRIMARY KEY,
    application_id       INT NOT NULL,
    step_order            INT NOT NULL,
    label                 VARCHAR(255) NOT NULL,
    state                 VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','active','done')),
    completed_at          DATETIME NULL,
    FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE mentor_bookings (
    booking_id   INT AUTO_INCREMENT PRIMARY KEY,
    mentor_id    INT NOT NULL,
    user_id      INT NOT NULL,
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status       VARCHAR(20) NOT NULL DEFAULT 'Requested' CHECK (status IN ('Requested','Confirmed','Completed','Cancelled')),
    FOREIGN KEY (mentor_id) REFERENCES mentors(mentor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"""CREATE TABLE payments (
    payment_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    application_id  INT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(10) NOT NULL DEFAULT 'USD',
    method          VARCHAR(20) NOT NULL CHECK (method IN ('Card','Mobile Money')),
    status          VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Completed','Failed','Refunded')),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (application_id) REFERENCES applications(application_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

"CREATE INDEX idx_universities_country ON universities(country_id);",
"CREATE INDEX idx_applications_user ON applications(user_id);",
"CREATE INDEX idx_vault_user ON vault_documents(user_id);",
"CREATE INDEX idx_payments_user ON payments(user_id);",
]

for stmt in DDL_STATEMENTS:
    c.execute(stmt)

# ---------------------------------------------------------------
# SEED DATA — identical to build_db.py's SQLite seed data
# ---------------------------------------------------------------

countries = ["Rwanda", "Uganda", "Kenya", "Tanzania", "Burundi", "DR Congo"]
c.executemany("INSERT INTO countries (name) VALUES (%s)", [(x,) for x in countries])
c.execute("SELECT country_id, name FROM countries")
country_id = {name: cid for cid, name in c.fetchall()}

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
        c.execute("INSERT IGNORE INTO document_types (name) VALUES (%s)", (name,))
        c.execute("SELECT document_type_id FROM document_types WHERE name=%s", (name,))
        doc_type_id[name] = c.fetchone()[0]
    return doc_type_id[name]

uni_id = {}
uni_scholarship_tags = {}
for (name, country, tuition, programs, link, partner, deadline, living_cost, benefits, docs, sch_tags) in universities:
    c.execute("""INSERT INTO universities (name, country_id, tuition, programs, website, is_partner, deadline, living_cost, partner_benefits)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
              (name, country_id[country], tuition, programs, link, partner, deadline, living_cost, benefits))
    university_id = c.lastrowid
    uni_id[name] = university_id
    for d in docs:
        dtid = get_doc_type(d)
        c.execute("INSERT IGNORE INTO university_required_documents (university_id, document_type_id) VALUES (%s,%s)", (university_id, dtid))
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
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (name, provider, category, amount, deadline, elig, link, partner))
    scholarship_id = c.lastrowid
    sch_id[name] = scholarship_id
    for d in docs:
        dtid = get_doc_type(d)
        c.execute("INSERT IGNORE INTO scholarship_required_documents (scholarship_id, document_type_id) VALUES (%s,%s)", (scholarship_id, dtid))
    for uni_name in elig_unis:
        c.execute("INSERT IGNORE INTO scholarship_universities (scholarship_id, university_id) VALUES (%s,%s)", (scholarship_id, uni_id[uni_name]))

tag_to_full = {
    "SFAR": "SFAR Student Loans",
    "Mastercard Foundation": "Mastercard Foundation Scholars Program",
    "BRD Minuza": "BRD Minuza Loan Portal",
    "DAAD": "DAAD Scholarships — East Africa",
    "Employer-Sponsored": None,
}
for uni_name, tags in uni_scholarship_tags.items():
    for t in tags:
        full = tag_to_full.get(t)
        if full and full in sch_id:
            c.execute("INSERT IGNORE INTO scholarship_universities (scholarship_id, university_id) VALUES (%s,%s)", (sch_id[full], uni_id[uni_name]))

mentors = [
    ("Aline U.", "UR Engineering Alum · Mastercard Scholar", "Essay review, interview prep", "Free · 20 min"),
    ("Eric N.", "CMU-Africa Student", "IT & Engineering applications", "Free · 20 min"),
    ("Divine K.", "AUCA Alum · SFAR recipient", "SFAR & BRD loan process walkthrough", "Free · 15 min"),
    ("Grace M.", "University of Nairobi Student", "Regional (Kenya) applications", "Free · 20 min"),
]
c.executemany("INSERT INTO mentors (name, role, focus_area, rate) VALUES (%s,%s,%s,%s)", mentors)

for d in ["Academic Transcript", "National ID / Passport", "Recommendation Letter", "Personal Statement"]:
    get_doc_type(d)

conn.commit()

# ---------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------
for tbl in ["countries","universities","scholarships","scholarship_universities","document_types",
            "university_required_documents","scholarship_required_documents","mentors"]:
    c.execute(f"SELECT COUNT(*) FROM `{tbl}`")
    n = c.fetchone()[0]
    print(f"{tbl}: {n} rows")

c.close()
conn.close()
print(f"MySQL database '{DATABASE}' built at {HOST}:{PORT}")
