# Gym Management App

A **local-only**, zero-cost gym management web application. Runs entirely on your machine with SQLite, local file storage, and no external services.

## Features

- Session-based login with **Admin** and **Staff** roles
- Member CRUD with optional photo uploads
- Flexible membership plans: **1–12 months** (renewal date uses proper month arithmetic)
- Status tracking: Active, Renewal Pending, Expired
- Dashboard with key metrics
- Search by phone or name
- Renewal tracking (today, next 7 days, expired, active)
- Payment updates with method, balance, and PT amount
- Reports page with **Excel (.xlsx)** exports (primary) and CSV alternatives, plus PDF summary

## Windows — Install and Run (No Python Required)

1. **Download** `GymManagerSetup.exe` from the [GitHub Actions](../../actions) build (artifact: **GymManagerSetup**) or from a release tag.
2. **Install** by double-clicking `GymManagerSetup.exe`.
3. **Launch** **Gym Manager** from the desktop shortcut (created automatically during install).
4. Your **browser opens automatically** — log in and start managing members.

Your data is stored locally and survives app updates:

| Data | Location |
|------|----------|
| Database | `%APPDATA%\GymManager\data\gym.db` |
| Member photos | `%APPDATA%\GymManager\uploads\members\` |

The app works fully offline. No internet connection is required after install.

### How to get GymManagerSetup.exe for your customer

**Option A — GitHub Actions (from macOS/Linux or any machine):**

1. Push this repo to GitHub.
2. Open **Actions** → **Build Windows EXE** → **Run workflow**.
3. When the run finishes, open the run → **Artifacts** → download **GymManagerSetup**.
4. Unzip if your browser wraps the download; the file inside is `GymManagerSetup.exe`.

**Option B — Build on a Windows PC (two commands):**

```bat
pip install -r requirements.txt -r requirements-build.txt
pyinstaller build.spec
cd installer && build-installer.bat
```

Output: `installer\Output\GymManagerSetup.exe`

**Handover to customer:** give them **only** `GymManagerSetup.exe` (and optionally `CUSTOMER_GUIDE.txt`). They do not need Python, Git, or any other files.

See [CUSTOMER_GUIDE.txt](CUSTOMER_GUIDE.txt) for the plain-text instructions to print or email alongside the installer.

### Building the Windows `.exe` yourself

**On Windows:**

```bat
pip install -r requirements.txt -r requirements-build.txt
pyinstaller build.spec
```

The app folder is created at `dist\GymManager\`. Double-click `GymManager.exe` to run (dev/testing only — use the installer for customers).

**Installer** (requires [Inno Setup 6+](https://jrsoftware.org/isinfo.php)):

```bat
cd installer
build-installer.bat
```

Output: `installer\Output\GymManagerSetup.exe`

**From macOS/Linux:** You cannot build a Windows `.exe` locally. Push a version tag (e.g. `v1.0.0`) or run the **Build Windows EXE** workflow manually on GitHub Actions, then download the **GymManagerSetup** artifact.

## Developer Quick Start (macOS / Linux / Windows)

```bash
cd gym-management-app

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Option A: standard dev server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Option B: same launcher the Windows exe uses
python launcher.py
```

Open **http://127.0.0.1:8000** in your browser.

## Default Login Credentials

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | `admin`  | `admin123` |
| Staff | `staff`  | `staff123` |

**Admin** can add, edit, delete members, upload photos, and update payments.

**Staff** can search/view members, add members, and update payments.

## Membership Plans

Plans are stored as an integer **1–12 months**:

| Months | Label |
|--------|-------|
| 1 | 1 Month |
| 2 | 2 Months |
| … | … |
| 11 | 11 Months |
| 12 | 12 Months (1 Year) |

Renewal date = date of joining + N months (e.g. Jan 31 + 1 month → Feb 28/29).

## Reports

Open **Reports** in the sidebar for grouped exports:

- **Member reports** — All members, renewal pending, expired (Excel or CSV)
- **Financial reports** — Monthly fee collection, personal training (Excel or CSV)
- **Overview** — PDF summary with counts and totals

Excel is recommended for gym owners on Windows; CSV remains available for imports into other tools.

## Project Structure

```
gym-management-app/
├── launcher.py              # Starts server + opens browser
├── build.spec               # PyInstaller packaging config
├── CUSTOMER_GUIDE.txt       # Plain-text handout for gym owner (5 steps)
├── requirements-build.txt   # PyInstaller (build only)
├── .github/workflows/
│   └── build-windows.yml    # CI build for Windows exe
├── installer/
│   ├── GymManager.iss       # Inno Setup script
│   └── build-installer.bat
├── app/
│   ├── main.py
│   ├── paths.py             # Dev vs AppData paths
│   ├── membership.py        # Plan months (1–12)
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── services/
│   ├── routers/
│   ├── templates/
│   └── static/
├── uploads/members/         # Dev-mode photo storage
├── gym.db                     # Dev-mode SQLite DB
├── requirements.txt
└── README.md
```

## Notes

- Database and sample members are seeded automatically on first run.
- In dev mode, photos are stored in `uploads/members/` and the DB in `gym.db`.
- Phone numbers must be unique.
- Personal training amount displays **NA** when not set.
- This app is designed for local use only — change the session secret before any non-local deployment.
