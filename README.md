# News Application

A Django news platform built for the HyperionDev Capstone (M06T08). Readers can browse and subscribe to publishers and independent journalists, journalists write articles and newsletters, and editors review and approve submissions before they go live.

## Features

- Custom user model with three roles: **Reader**, **Editor**, **Journalist**
- Role-based permissions enforced through Django Groups
- Readers can subscribe to Publishers and/or individual Journalists
- Editors review pending articles and approve them
- On approval: subscribers get emailed, and the article is logged to an internal `/api/approved/` endpoint (simulating external distribution)
- A full REST API (Django REST Framework) with token authentication and role-based permissions
- 12 automated tests covering permissions, subscriptions, and the approval flow
- Runs on MariaDB

## Models

| Model | Notes |
|---|---|
| `CustomUser` | Extends Django's `AbstractUser`. Has a `role` field, plus subscription fields (Readers only). |
| `Publisher` | Has its own Editors and Journalists (M2M). |
| `Article` | Belongs to an `author` (always a journalist). `publisher` is optional — set it for publisher content, leave blank for independent articles. |
| `Newsletter` | A collection of articles, created by a journalist or editor. |

## Roles and permissions

| Role | Can do |
|---|---|
| Reader | View articles and newsletters |
| Editor | View, update, and delete any article/newsletter; approve pending articles |
| Journalist | Create, view, update, and delete their own articles/newsletters |

A signal (`news/signals.py`) automatically assigns each user to the matching Group whenever their role is set or changed, and clears subscription fields if they become a Journalist.

## Front-end pages

The app also ships a minimal front end so an account can be created and used without touching Django admin:

| URL | Purpose |
|---|---|
| `/register/` | Sign up and pick a role (Reader, Editor, Journalist). Saving the form logs you in immediately. |
| `/login/` | Log in with an existing account. |
| `/logout/` | Log out (POST only). |
| `/` | Home page - shows your role and where to go next once logged in. |
| `/editor/pending/` | Editors only: review and approve pending articles. |

Registering just creates the `CustomUser` with the chosen role; the existing `sync_user_role` signal
handles putting the account in the right Group (and therefore the right permissions), so there's no
separate group-assignment step in the registration view itself.

## Setup (venv)

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
```

Set the required environment variables (see **Configuration and secrets** below), then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The `migrate` step also creates the Reader/Editor/Journalist Groups with their permissions automatically (see `news/migrations/0002_create_groups.py`) — no manual setup needed.

### Configuration and secrets

Settings that used to be hardcoded in `newsproject/settings.py` (secret key, debug flag, allowed
hosts, and the database connection) are now read from environment variables:

| Variable                | Purpose                                    | Default (dev)                    |
|--------------------------|---------------------------------------------|------------------------------------|
| `DJANGO_SECRET_KEY`      | Django's cryptographic signing key         | an insecure fallback key          |
| `DJANGO_DEBUG`           | `True`/`False` — enables Django debug mode | `True`                            |
| `DJANGO_ALLOWED_HOSTS`   | Comma-separated list of allowed hostnames  | `localhost,127.0.0.1`             |
| `DATABASE_ENGINE`        | Django DB backend                          | `django.db.backends.mysql`        |
| `DATABASE_NAME`          | Database name                              | `newsapp_db`                      |
| `DATABASE_USER`          | Database user                              | `root`                            |
| `DATABASE_PASSWORD`      | Database password                          | *(empty)*                         |
| `DATABASE_HOST`          | Database host                              | `localhost`                       |
| `DATABASE_PORT`          | Database port                              | `3306`                            |

**Do not commit real secret values to the repo.** Export them in your shell, or put them in a
local `.env` file that's excluded from git by `.gitignore`. For a quick local check without a real
MySQL/MariaDB server (e.g. before you've set one up), you can point at SQLite instead:

```bash
export DATABASE_ENGINE=django.db.backends.sqlite3   # macOS/Linux
set DATABASE_ENGINE=django.db.backends.sqlite3       # Windows (cmd)
```

### Database

This project runs on MariaDB by default. Create a database (matching `DATABASE_NAME`) and a user
with access to it, set the `DATABASE_*` environment variables above to match, then run `migrate`.

## API endpoints

| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/articles/` | Any authenticated user — approved articles only |
| GET | `/api/articles/subscribed/` | Reader — only their subscribed content |
| GET | `/api/articles/<id>/` | Any authenticated user |
| POST | `/api/articles/` | Journalists only |
| PUT | `/api/articles/<id>/` | Editors (any article) or the Journalist who wrote it |
| DELETE | `/api/articles/<id>/` | Editors (any article) or the Journalist who wrote it |
| POST | `/api/token/` | Obtain an auth token (username + password) |

Authenticate API requests with a token in the header:
```
Authorization: Token <your_token_here>
```

### Editor approval

Editors review pending articles at `/editor/pending/` and approve them there. Approval triggers an email to subscribers and a POST to `/api/approved/`.

## Running with Docker

The easiest way to run the full stack (app + MariaDB) is with docker-compose:

```bash
docker-compose up --build
```

This starts a MariaDB container and the Django app (which waits for the database, then runs
migrations automatically before serving). Visit `http://localhost:8000/` once it's up.

**Change the placeholder passwords** in `docker-compose.yml` before using this for anything beyond
local testing.

To build and run just the app image against a database you're managing yourself:

```bash
docker build -t news-application .
docker run -p 8000:8000 \
  -e DJANGO_SECRET_KEY="your-own-secret-key" \
  -e DATABASE_HOST=<your-db-host> \
  -e DATABASE_PASSWORD=<your-db-password> \
  news-application
```

If you don't have Docker installed locally, you can also test the image using the
[Docker playground](https://labs.play-with-docker.com/).

## Documentation

API and code documentation is generated with Sphinx from docstrings in the `news` app. The built
HTML is included in the repo at `docs/_build/html/index.html`. To regenerate it, from the `docs`
folder with the virtual environment activated:

```bash
make clean
make html
```

## Running the tests

```bash
python manage.py test news
```

12 tests cover: authenticated access per role, reader subscription filtering, journalist article creation, editor update/delete permissions, newsletter creation, and the approval flow's email + API logging (mocked, no real network calls during testing).

## Design notes

- **Article-Publisher relationship**: `publisher` is nullable on `Article` so a single `author` field can represent both independent journalism (publisher blank) and publisher-affiliated content (publisher set), satisfying the requirement that an article be tied to a journalist *or* a publisher.
- **Clearing role-specific fields**: the brief asks for Reader/Journalist fields to be set to `None` when the other role is active. Since `Article.author` and `Newsletter.author` are required foreign keys, they can't be nulled without deleting content — so the signal clears the Reader-only subscription fields instead, and relies on Group permissions to restrict what a user can *do* with their role going forward.
