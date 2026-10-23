# CampusMate — Smart Campus Management System

**Tagline:** Your Campus. Connected.

CampusMate is a local-first college portal built for a BCA college project using Python, Flask, SQLite, HTML, CSS, and vanilla JavaScript. It brings student dashboards, faculty schedules, a digital notice board, user management, and timetable administration into one responsive application.

## Features

- Student registration, secure password hashing, login, logout, and role-based dashboards.
- Separate Student, Teacher, and Administrator experiences.
- SQLite storage that persists across application restarts.
- Notice board with category/search filters, audience targeting, draft/published states, priorities, event dates, and admin create/edit/delete features.
- Daily and weekly timetable views with course/semester/section filtering.
- Admin creation/deactivation of users and teacher accounts.
- Profile editing and password change.
- CSRF protection, server-side role checks, responsive mobile layout, and helpful error pages.
- Repeatable database initialization and demo-data seeding.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer (Python 3.12 is a good choice).
- Visual Studio Code (recommended, but not required to run the site).
- Internet access for the initial Python package installation. The application itself uses no paid or external API.

To check whether Python is installed, open Command Prompt and run:

```bat
py --version
```

If that command is unavailable, try:

```bat
python --version
```

If neither works, install Python from https://www.python.org/downloads/windows/ and enable **Add Python to PATH** during installation. Reopen VS Code after installing Python.

## First-time setup (recommended)

1. Download `CampusMate_Complete_Project.zip` and extract it fully.
2. Open VS Code and choose **File → Open Folder**.
3. Select the extracted `CampusMate` folder (the folder containing `app.py`).
4. In File Explorer, double-click `setup_and_run.bat`, or run it from the VS Code terminal:

```bat
setup_and_run.bat
```

The script checks for Python, creates a local `.venv` virtual environment, installs the packages in `requirements.txt`, creates the SQLite tables, seeds demo data without duplicating records, and starts Flask. Keep the terminal open while using the website.

Open this address in your browser:

**http://127.0.0.1:5000**

Stop the server with **Ctrl+C** in the terminal.

## Subsequent launches

After setup is complete, open the `CampusMate` folder and run:

```bat
run.bat
```

The run script uses the existing virtual environment and does not reinstall packages each time. It initializes the database only if the database file is missing.

## Manual setup (optional)

Open a terminal in the project folder and run these commands in order:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe init_db.py
.venv\Scripts\python.exe seed_data.py
.venv\Scripts\python.exe app.py
```

If the `py` launcher is not available but `python` is, replace `py -3` with `python`. To run automated tests after installing the requirements, run:

```bat
.venv\Scripts\python.exe -m pytest -q
```

## Development demo accounts

The initial demo seed creates the following fictional development accounts. Each demo password is `CampusDemo123!`.

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@campusmate.local` | `CampusDemo123!` |
| Teacher | `teacher@campusmate.local` | `CampusDemo123!` |
| Student | `student@campusmate.local` | `CampusDemo123!` |

These credentials are for local project demonstration only. Change them and set a strong `CAMPUSMATE_SECRET_KEY` before any deployment accessible to other people. The demo seeder creates these accounts only when the matching email is not already present; it will not overwrite an existing account's password.

Public registration creates student accounts only. To create another teacher account, log in as the administrator, open **User management**, and use the teacher-account form.

## Database and saved data

The database is stored in `instance/campusmate.db`. User profiles, notices, and timetable entries are saved there. The site does not reset or delete the database when it starts. The demo seed avoids creating duplicate demo records and adds the example notices/timetable entries only when those tables are empty.

To make a backup, stop the app and copy `instance/campusmate.db` somewhere safe.

### Resetting demo data

There is deliberately no destructive “reset database” action in the website. To fully reset a local demo, stop the app, back up the database if needed, then delete `instance/campusmate.db`. Run `init_db.py` and `seed_data.py` again using the virtual-environment Python command. **Deleting this file permanently removes all local accounts, notices, and timetable edits**, so do this only when you really want a fresh demo.

## Project structure

```text
CampusMate/
├── app.py                  # Flask app, database models, and web routes
├── init_db.py              # Non-destructive table initialization
├── seed_data.py            # Idempotent fictional demo data
├── requirements.txt        # Python dependencies
├── setup_and_run.bat       # Initial Windows setup and launch
├── run.bat                 # Subsequent launch
├── routes/                 # Reserved for future route modularization
├── templates/              # Jinja2 HTML templates
├── static/css/             # Responsive styling
├── static/js/              # Menu, confirmations, and UI behaviors
├── tests/test_app.py       # Basic automated tests
└── instance/campusmate.db  # Created locally during initialization
```

For simplicity of installation and demonstration, this MVP keeps the route handlers and ORM models in `app.py`. The `routes` directory is included for future modularization; no missing route module is required to run the current app.

## Troubleshooting

- **Python is not recognized:** install Python 3, enable PATH access, and reopen the terminal.
- **Package installation fails:** confirm internet access, then retry `setup_and_run.bat`. If a terminal is using an incompatible Python version, install Python 3.12 and use its launcher.
- **`Address already in use`:** another app is using port 5000. Stop the other process or open a new terminal and set `PORT=5001` before launching, then visit `http://127.0.0.1:5001`.
- **Login fails:** use one of the demo email addresses and the demo password exactly as listed above. If you changed the password previously, the seed process will not reset it.
- **Database errors after moving files:** keep the folder structure intact and run `init_db.py` from the project folder; the database path is relative to the application project.
- **Browser looks unstyled:** confirm `static/css/style.css` and `static/css/dashboard.css` exist and refresh the browser.
- **Server is stopped:** run `run.bat` again; your database changes are retained.

## Security and deployment notes

This project is a college-project MVP, not an audited production campus system. It uses password hashing, server-side authorization, CSRF protection, basic input checks, and HTTP-only session cookies. The default secret key is deliberately a local-development fallback. For any deployment, set `CAMPUSMATE_SECRET_KEY` to a long random secret, configure HTTPS and secure cookies, use a production WSGI server, review all security settings, and change/remove demo accounts. Do not expose Flask's development server directly to the public internet.

## Tests

The automated test suite covers basic startup, authentication, role protection, registration duplicate checking, notice visibility/creation, and timetable permissions. Run:

```bat
.venv\Scripts\python.exe -m pytest -q
```

The setup script's successful startup is not a replacement for running the tests on your own computer.
