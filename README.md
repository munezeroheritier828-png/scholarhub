# Scholar Hub — full-stack project

Everything from the original prototype, split into three layers that talk
to each other:

```
scholarhub-fullstack/
├── database/
│   ├── scholarhub.db               SQLite database, already built and seeded (default)
│   ├── schema_and_data.sql         Portable SQLite SQL dump
│   ├── build_db.py                 Rebuilds scholarhub.db from scratch
│   ├── mysql_schema_and_data.sql   MySQL/MariaDB dump — import directly with mysql <
│   └── build_db_mysql.py           Builds + seeds a MySQL/MariaDB database instead
├── backend/
│   ├── app.py                      Flask REST API — SQLite backend (default)
│   ├── app_mysql.py                Same API, backed by MySQL/MariaDB instead
│   ├── requirements.txt
│   └── requirements-mysql.txt
└── frontend/
    ├── index.html                   Your original page, rewired to be backend-only
    │                                for user data (see note below — no localStorage)
    └── style.css                    A stand-in stylesheet — see note below
```

## Two database options

**SQLite (default, zero setup)** — `database/scholarhub.db` is already
built and seeded. Run `backend/app.py` and you're done; nothing else to
install or configure.

**MySQL / MariaDB** — if you'd rather run this against a real MySQL
server (locally, a VM, RDS, PlanetScale, etc.), use:
```
cd backend
pip install -r requirements-mysql.txt
```
Then either import the ready-made dump directly:
```
mysql -u root -p -e "CREATE DATABASE scholarhub CHARACTER SET utf8mb4;"
mysql -u root -p scholarhub < ../database/mysql_schema_and_data.sql
```
or build it from the Python script instead (same seed data; useful if you
want to point at a fresh empty server and let it create the database for
you):
```
MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=yourpassword \
  python ../database/build_db_mysql.py
```
Then run the MySQL-backed API (same env vars the build script used):
```
MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=yourpassword \
  python app_mysql.py
```
This was tested end to end against a real MariaDB 10.11 server before
being handed to you: schema creation, all 12 universities and 7
scholarships seeded with their many-to-many links intact, a real signup,
a wrong-password login correctly rejected, profile update, vault toggle,
application creation, and a payment record all round-tripped correctly.
`app_mysql.py` serves the exact same `/api/...` routes as `app.py` — the
frontend doesn't know or care which one is running underneath.

Connection settings (same env vars for both the build script and
`app_mysql.py`):
| Variable | Default |
|---|---|
| `MYSQL_HOST` | `127.0.0.1` |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | *(empty)* |
| `MYSQL_DATABASE` | `scholarhub` |

## How the pieces connect

- **database/** is the single source of truth: universities, scholarships,
  the many-to-many links between them, mentors, users, profiles, the
  document vault, the application tracker, and payment records — in
  either SQLite or MySQL, your choice.
- **backend/app.py** (or **app_mysql.py**) reads and writes that database
  and exposes it as a JSON API (`/api/universities`, `/api/scholarships`,
  `/api/auth/login`, `/api/profile`, `/api/vault`, `/api/applications`,
  `/api/mentor-bookings`, `/api/payments`, …). Both serve identical routes
  with identical response shapes.
- **frontend/index.html** is your original file, rewired to be
  backend-only for anything user-specific. **No `localStorage`,
  `sessionStorage`, or cookies are used anywhere.** Login and signup are
  real database checks now (the original file set you as "logged in" for
  *any* well-formatted email/password — that's fixed). Profile, the
  document vault, and the application tracker are all read from and
  written to the database directly. Refreshing the page signs you out on
  purpose, since nothing is cached in the browser to restore — the
  database is the only place state lives. The public catalog
  (universities/scholarships/mentors) still has an offline fallback so
  the page isn't blank if the backend is briefly down, since that's just
  public read-only data, not something tied to a person.

## Running it

One command runs the whole thing — the backend serves the frontend too,
so there's a single origin and no separate static server:
```
cd backend
pip install -r requirements.txt      # or requirements-mysql.txt for the MySQL path
python app.py                        # or app_mysql.py
```
Then open **http://localhost:5000** — that's it. `/` serves `index.html`,
`/style.css` and any other frontend file are served alongside it, and
`/api/...` is the same server. This also fixes the earlier "page loads
with no styling" issue: that happened when `index.html` was opened
directly (`file://`), which can silently fail to load `style.css`
depending on the browser. Loading everything through Flask removes that
failure mode entirely.

If you ever split frontend and backend onto different hosts, set
`window.SCHOLAR_HUB_API = 'https://your-api.example.com/api'` in a
`<script>` tag before `index.html`'s main script runs.

## Two things worth knowing

- **`style.css` is a stand-in.** The uploaded project referenced
  `style.css` but didn't include the file, so this repo ships a functional
  placeholder covering every class the markup uses. If you have the real
  stylesheet, drop it in over this one.
- **The Pay button was previously dead code.** `selectPaymentMethod()` and
  `processProfessionalPayment()` were called by `onclick=` handlers in the
  payment section but were never defined anywhere in the original file.
  They're now implemented and wired to `POST /api/payments` — which stores
  only the amount, currency, and method. Card number and CVV fields are
  never read or transmitted anywhere; wire a real processor (Stripe,
  Flutterwave, Paystack, etc.) before taking real payments.

## Security notes for production

- The backend's auth is a minimal in-memory bearer-token scheme, fine for
  local development. Swap it for signed JWTs or server-side sessions
  before deploying. This also means sessions don't survive a backend
  restart or scale across multiple server processes — fine for one
  dev/demo instance, not for production.
- Both `app.py` and `app_mysql.py` run Flask's development server. Use
  gunicorn/uwsgi behind a reverse proxy in production.
- Restrict CORS (`flask_cors.CORS(app)` currently allows all origins) to
  your real frontend domain once you're not developing locally.
- If you use MySQL, set your own database credentials — don't reuse any
  example username/password from a README anywhere real.
