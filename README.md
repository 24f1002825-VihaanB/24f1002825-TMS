# Trekking Management Application

A web application for managing trekking activities, built as part of the IIT Madras MAD-1 course.

## Roles

- **Admin** — Manages treks, staff, and users
- **Trek Staff** — Manages assigned treks and participants
- **Trekker (User)** — Browses and books treks

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite, SQLAlchemy ORM
- **Frontend**: HTML5, Jinja2, Bootstrap 5, CSS
- **Auth**: Flask Sessions, Werkzeug Password Hashing

## Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The database and admin account are created automatically on first run.

## Default Admin Credentials

- **Email**: admin@trekking.com
- **Password**: admin123
