BEGIN TRANSACTION;
CREATE TABLE application_steps (
    application_step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id       INTEGER NOT NULL REFERENCES applications(application_id) ON DELETE CASCADE,
    step_order            INTEGER NOT NULL,
    label                 TEXT NOT NULL,
    state                 TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','active','done')),
    completed_at          TEXT
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
CREATE TABLE countries (
    country_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE
);
INSERT INTO "countries" VALUES(1,'Rwanda');
INSERT INTO "countries" VALUES(2,'Uganda');
INSERT INTO "countries" VALUES(3,'Kenya');
INSERT INTO "countries" VALUES(4,'Tanzania');
INSERT INTO "countries" VALUES(5,'Burundi');
INSERT INTO "countries" VALUES(6,'DR Congo');
CREATE TABLE document_types (
    document_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL UNIQUE
);
INSERT INTO "document_types" VALUES(1,'Academic Transcript');
INSERT INTO "document_types" VALUES(2,'National ID / Passport');
INSERT INTO "document_types" VALUES(3,'Recommendation Letter');
INSERT INTO "document_types" VALUES(4,'Personal Statement');
CREATE TABLE mentor_bookings (
    booking_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id    INTEGER NOT NULL REFERENCES mentors(mentor_id),
    user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    status       TEXT NOT NULL DEFAULT 'Requested' CHECK (status IN ('Requested','Confirmed','Completed','Cancelled'))
);
CREATE TABLE mentors (
    mentor_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    role       TEXT,
    focus_area TEXT,
    rate       TEXT
);
INSERT INTO "mentors" VALUES(1,'Aline U.','UR Engineering Alum · Mastercard Scholar','Essay review, interview prep','Free · 20 min');
INSERT INTO "mentors" VALUES(2,'Eric N.','CMU-Africa Student','IT & Engineering applications','Free · 20 min');
INSERT INTO "mentors" VALUES(3,'Divine K.','AUCA Alum · SFAR recipient','SFAR & BRD loan process walkthrough','Free · 15 min');
INSERT INTO "mentors" VALUES(4,'Grace M.','University of Nairobi Student','Regional (Kenya) applications','Free · 20 min');
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
CREATE TABLE scholarship_required_documents (
    scholarship_id    INTEGER NOT NULL REFERENCES scholarships(scholarship_id) ON DELETE CASCADE,
    document_type_id  INTEGER NOT NULL REFERENCES document_types(document_type_id) ON DELETE CASCADE,
    PRIMARY KEY (scholarship_id, document_type_id)
);
INSERT INTO "scholarship_required_documents" VALUES(1,1);
INSERT INTO "scholarship_required_documents" VALUES(1,2);
INSERT INTO "scholarship_required_documents" VALUES(2,1);
INSERT INTO "scholarship_required_documents" VALUES(2,2);
INSERT INTO "scholarship_required_documents" VALUES(3,1);
INSERT INTO "scholarship_required_documents" VALUES(3,2);
INSERT INTO "scholarship_required_documents" VALUES(3,3);
INSERT INTO "scholarship_required_documents" VALUES(3,4);
INSERT INTO "scholarship_required_documents" VALUES(4,1);
INSERT INTO "scholarship_required_documents" VALUES(4,2);
INSERT INTO "scholarship_required_documents" VALUES(4,3);
INSERT INTO "scholarship_required_documents" VALUES(5,1);
INSERT INTO "scholarship_required_documents" VALUES(5,2);
INSERT INTO "scholarship_required_documents" VALUES(6,1);
INSERT INTO "scholarship_required_documents" VALUES(6,2);
INSERT INTO "scholarship_required_documents" VALUES(6,4);
INSERT INTO "scholarship_required_documents" VALUES(7,1);
INSERT INTO "scholarship_required_documents" VALUES(7,2);
CREATE TABLE scholarship_universities (
    scholarship_id INTEGER NOT NULL REFERENCES scholarships(scholarship_id) ON DELETE CASCADE,
    university_id  INTEGER NOT NULL REFERENCES universities(university_id) ON DELETE CASCADE,
    PRIMARY KEY (scholarship_id, university_id)
);
INSERT INTO "scholarship_universities" VALUES(1,1);
INSERT INTO "scholarship_universities" VALUES(1,3);
INSERT INTO "scholarship_universities" VALUES(1,5);
INSERT INTO "scholarship_universities" VALUES(1,4);
INSERT INTO "scholarship_universities" VALUES(2,3);
INSERT INTO "scholarship_universities" VALUES(2,5);
INSERT INTO "scholarship_universities" VALUES(3,1);
INSERT INTO "scholarship_universities" VALUES(3,2);
INSERT INTO "scholarship_universities" VALUES(3,6);
INSERT INTO "scholarship_universities" VALUES(4,6);
INSERT INTO "scholarship_universities" VALUES(4,7);
INSERT INTO "scholarship_universities" VALUES(4,10);
INSERT INTO "scholarship_universities" VALUES(7,1);
INSERT INTO "scholarship_universities" VALUES(7,2);
INSERT INTO "scholarship_universities" VALUES(7,3);
INSERT INTO "scholarship_universities" VALUES(3,8);
INSERT INTO "scholarship_universities" VALUES(1,11);
INSERT INTO "scholarship_universities" VALUES(4,12);
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
INSERT INTO "scholarships" VALUES(1,'SFAR Student Loans','Government of Rwanda','Government','Tuition + living stipend','Rolling, annual cycle','Any accredited Rwandan institution','https://sfar.gov.rw',1);
INSERT INTO "scholarships" VALUES(2,'BRD Minuza Loan Portal','Development Bank of Rwanda','Government','Varies by program','Rolling','University of Kigali, AUCA, and partner institutions','https://minuza.brd.rw/',1);
INSERT INTO "scholarships" VALUES(3,'Mastercard Foundation Scholars Program','Mastercard Foundation','NGO','Full tuition + stipend','Varies by partner university','UR, CMU-Africa, Makerere (partner institutions only)',NULL,1);
INSERT INTO "scholarships" VALUES(4,'DAAD Scholarships — East Africa','DAAD (Germany)','International','Full funding + travel','Varies by program','Specific graduate programs, partner universities',NULL,0);
INSERT INTO "scholarships" VALUES(5,'District Community Bursary','Local district fund (example)','Local','Partial tuition support','Set by district office','Any accredited institution, district residents',NULL,0);
INSERT INTO "scholarships" VALUES(6,'Twiga Capital Future Talent Award','Twiga Capital (employer-sponsored)','Employer','Full tuition + guaranteed internship','Applications open termly','Business & IT programs, any accredited institution — includes a post-graduation internship offer',NULL,0);
INSERT INTO "scholarships" VALUES(7,'Virunga Works Engineering Award','Virunga Works (employer-sponsored)','Employer','Partial tuition + job placement track','Rolling','Engineering programs at UR, CMU-Africa, University of Kigali',NULL,0);
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
INSERT INTO "universities" VALUES(1,'University of Rwanda (UR)',1,'≈ 600,000 – 1,200,000 RWF / yr','Engineering, Medicine, Business, Education, Sciences','https://www.ur.ac.rw',1,'Rolling — intake in Sept & Jan','≈ 150,000 – 250,000 RWF / month','Priority review · Application fee waiver · Exclusive scholarship matching');
INSERT INTO "universities" VALUES(2,'Carnegie Mellon University Africa',1,'Contact admissions for tuition & aid','ICT, Electrical & Computer Engineering, Information Technology','https://africa.engineering.cmu.edu',1,'Jan 15 (Fall intake)','Campus housing available — contact admissions','Priority review · Mastercard Scholars pathway support');
INSERT INTO "universities" VALUES(3,'University of Kigali',1,'≈ 700,000 – 1,500,000 RWF / yr','Law, Business, IT, Public Health','https://www.uok.ac.rw',1,'Rolling','≈ 180,000 – 280,000 RWF / month','Priority review · BRD Minuza guidance · Fee waiver for eligible applicants');
INSERT INTO "universities" VALUES(4,'Mount Kenya University Rwanda',1,'≈ 650,000 – 1,300,000 RWF / yr','Business, Education, Health Sciences, Journalism','https://mku.ac.rw',0,'Rolling','≈ 150,000 – 250,000 RWF / month',NULL);
INSERT INTO "universities" VALUES(5,'Adventist University of Central Africa (AUCA)',1,'≈ 600,000 – 1,100,000 RWF / yr','Theology, Business, Nursing, Computer Science','https://www.auca.ac.rw',1,'Rolling','≈ 140,000 – 220,000 RWF / month','Priority review · BRD Minuza guidance');
INSERT INTO "universities" VALUES(6,'Makerere University',2,'Varies by program — see admissions','Medicine, Engineering, Agriculture, Arts','https://www.mak.ac.ug',0,'See admissions calendar','Varies — Kampala',NULL);
INSERT INTO "universities" VALUES(7,'Kyambogo University',2,'Varies by program — see admissions','Engineering, Education, Vocational Studies','https://kyu.ac.ug',0,'See admissions calendar','Varies — Kampala',NULL);
INSERT INTO "universities" VALUES(8,'University of Nairobi',3,'Varies by program — see admissions','Law, Medicine, Engineering, Business','https://www.uonbi.ac.ke',0,'See admissions calendar','Varies — Nairobi',NULL);
INSERT INTO "universities" VALUES(9,'Strathmore University',3,'Varies by program — see admissions','Business, Law, IT, Actuarial Science','https://strathmore.edu',0,'See admissions calendar','Varies — Nairobi',NULL);
INSERT INTO "universities" VALUES(10,'University of Dar es Salaam',4,'Varies by program — see admissions','Engineering, Law, Social Sciences','https://www.udsm.ac.tz',0,'See admissions calendar','Varies — Dar es Salaam',NULL);
INSERT INTO "universities" VALUES(11,'University of Burundi',5,'Varies by program — see admissions','Medicine, Agronomy, Law, Sciences',NULL,0,'See admissions','Varies',NULL);
INSERT INTO "universities" VALUES(12,'University of Kinshasa',6,'Varies by program — see admissions','Medicine, Law, Engineering, Economics',NULL,0,'See admissions','Varies',NULL);
CREATE TABLE university_required_documents (
    university_id    INTEGER NOT NULL REFERENCES universities(university_id) ON DELETE CASCADE,
    document_type_id INTEGER NOT NULL REFERENCES document_types(document_type_id) ON DELETE CASCADE,
    PRIMARY KEY (university_id, document_type_id)
);
INSERT INTO "university_required_documents" VALUES(1,1);
INSERT INTO "university_required_documents" VALUES(1,2);
INSERT INTO "university_required_documents" VALUES(2,1);
INSERT INTO "university_required_documents" VALUES(2,2);
INSERT INTO "university_required_documents" VALUES(2,3);
INSERT INTO "university_required_documents" VALUES(3,1);
INSERT INTO "university_required_documents" VALUES(3,2);
INSERT INTO "university_required_documents" VALUES(4,1);
INSERT INTO "university_required_documents" VALUES(4,2);
INSERT INTO "university_required_documents" VALUES(5,1);
INSERT INTO "university_required_documents" VALUES(5,2);
INSERT INTO "university_required_documents" VALUES(6,1);
INSERT INTO "university_required_documents" VALUES(6,2);
INSERT INTO "university_required_documents" VALUES(6,3);
INSERT INTO "university_required_documents" VALUES(7,1);
INSERT INTO "university_required_documents" VALUES(7,2);
INSERT INTO "university_required_documents" VALUES(8,1);
INSERT INTO "university_required_documents" VALUES(8,2);
INSERT INTO "university_required_documents" VALUES(9,1);
INSERT INTO "university_required_documents" VALUES(9,2);
INSERT INTO "university_required_documents" VALUES(9,3);
INSERT INTO "university_required_documents" VALUES(10,1);
INSERT INTO "university_required_documents" VALUES(10,2);
INSERT INTO "university_required_documents" VALUES(11,1);
INSERT INTO "university_required_documents" VALUES(11,2);
INSERT INTO "university_required_documents" VALUES(12,1);
INSERT INTO "university_required_documents" VALUES(12,2);
CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,          -- never store plaintext passwords
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);
CREATE TABLE vault_documents (
    vault_document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    document_type_id  INTEGER NOT NULL REFERENCES document_types(document_type_id),
    is_uploaded       INTEGER NOT NULL DEFAULT 0 CHECK (is_uploaded IN (0,1)),
    uploaded_at       TEXT,
    UNIQUE (user_id, document_type_id)
);
CREATE INDEX idx_universities_country ON universities(country_id);
CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_vault_user ON vault_documents(user_id);
CREATE INDEX idx_payments_user ON payments(user_id);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('countries',6);
INSERT INTO "sqlite_sequence" VALUES('universities',12);
INSERT INTO "sqlite_sequence" VALUES('document_types',4);
INSERT INTO "sqlite_sequence" VALUES('scholarships',7);
INSERT INTO "sqlite_sequence" VALUES('mentors',4);
COMMIT;
