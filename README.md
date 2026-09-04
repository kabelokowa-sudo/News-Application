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

## Setup

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The `migrate` step also creates the Reader/Editor/Journalist Groups with their permissions automatically (see `news/migrations/0002_create_groups.py`) — no manual setup needed.

### Database

This project runs on MariaDB. Update `DATABASES` in `newsproject/settings.py` with your own credentials, and make sure a database named `newsapp_db` (or your chosen name) exists before running `migrate`.

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

## Running the tests

```bash
python manage.py test news
```

12 tests cover: authenticated access per role, reader subscription filtering, journalist article creation, editor update/delete permissions, newsletter creation, and the approval flow's email + API logging (mocked, no real network calls during testing).

## Design notes

- **Article-Publisher relationship**: `publisher` is nullable on `Article` so a single `author` field can represent both independent journalism (publisher blank) and publisher-affiliated content (publisher set), satisfying the requirement that an article be tied to a journalist *or* a publisher.
- **Clearing role-specific fields**: the brief asks for Reader/Journalist fields to be set to `None` when the other role is active. Since `Article.author` and `Newsletter.author` are required foreign keys, they can't be nulled without deleting content — so the signal clears the Reader-only subscription fields instead, and relies on Group permissions to restrict what a user can *do* with their role going forward.
