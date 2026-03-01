# AI Buddy — Backend Documentation

**Version:** 0.1.0  
**Python:** ≥ 3.12  
**Package manager:** Poetry  
**Scope:** Backend only — libraries, tools, APIs, database, AI integration, and project structure.

---

## 1. Overview

The AI Buddy backend is a **Django REST API** that provides authentication, user profiles, email verification, password reset, chat (AI and direct), and a matching system. It uses **PostgreSQL** for data, **JWT** for auth, **OpenAI** (optional) for the AI tutor in chats, and **Gmail SMTP** for sending verification and reset codes. The frontend is a separate React app that calls this API.

---

## 2. Libraries & Tools

### 2.1 Core Framework

| Library | Version | Purpose |
|---------|---------|--------|
| **Django** | ≥ 6.0.2, < 7.0 | Web framework: URL routing, ORM, admin, middleware, settings. |
| **djangorestframework (DRF)** | ≥ 3.16.1, < 4.0 | REST API: views, serializers, permissions, authentication. |

### 2.2 Authentication

| Library | Version | Purpose |
|---------|---------|--------|
| **djangorestframework-simplejwt** | ≥ 5.5.1, < 6.0 | JWT access and refresh tokens; token blacklist for logout. |

- Login returns `access` and `refresh` tokens.
- Protected endpoints use `Authorization: Bearer <access_token>`.
- Logout sends refresh token to blacklist.

### 2.3 Database

| Library | Version | Purpose |
|---------|---------|--------|
| **psycopg2-binary** | ≥ 2.9.11, < 3.0 | PostgreSQL adapter for Django. |

- All persistent data (users, chats, messages, invites, interests) is stored in PostgreSQL.
- Connection settings come from environment variables (see § 5).

### 2.4 AI (Chat Tutor)

| Library | Version | Purpose |
|---------|---------|--------|
| **openai** | ≥ 2.24.0, < 3.0 | OpenAI API client for the AI tutor in chats. |

- Used for: generating topics, tasks, hints, evaluating answers, chat replies, and progress summaries.
- If `OPENAI_API_KEY` is not set or the API fails, the backend falls back to a **built-in non-AI tutor** (rule-based topic/task/hint/evaluate and simple chat reply).
- Optional env: `OPENAI_MODEL` (default: `gpt-4o-mini`).

### 2.5 Configuration & API Docs

| Library | Version | Purpose |
|---------|---------|--------|
| **environs** | ≥ 14.6.0, < 15.0 | Load settings from `.env` (SECRET_KEY, DEBUG, DB_*, EMAIL_*, etc.). |
| **drf-spectacular** | ≥ 0.29.0, < 0.30 | OpenAPI 3 schema and Swagger/ReDoc UI for the API. |

- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`
- Schema: `/api/schema/`

### 2.6 Development / Type Hints

| Library | Version | Purpose |
|---------|---------|--------|
| **djangorestframework-stubs** | ≥ 3.16.8, < 4.0 | Type stubs for DRF (optional, for static analysis). |

---

## 3. Project Structure (Apps)

| App | Role |
|-----|------|
| **core** | Django project config: `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`. Root URL routing, API docs, admin. |
| **user** | Custom user model, registration (email → verify → password → complete), login/logout, profile, password reset, forgot-password flow, interest options. |
| **chats** | Chat and message models; AI and direct chats; message handling and AI commands (#topic, #task, #hint, #answer, #evaluate); OpenAI integration with fallback tutor. |
| **matching** | Chat invites (send, accept, reject); best-match and candidates by shared interests. |

---

## 4. API Endpoints (Summary)

### 4.1 Auth (`/api/auth/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `interests/` | GET | List interest options (for registration/complete). |
| `register/email/` | POST | Step 1: send 6-digit code to email. |
| `register/verify/` | POST | Step 2: verify code, return `session_token`. |
| `register/password/` | POST | Step 3: set password with `session_token`. |
| `register/complete/` | POST | Step 4: username, first/last name, bio, interests; activate user. |
| `login/` | POST | Username + password → access + refresh tokens. |
| `logout/` | POST | Blacklist refresh token (body: `refresh`). |
| `profile/` | GET | Current user profile (authenticated). |
| `password/reset/` | POST | Change password when logged in (old + new). |
| `password/forgot/email/` | POST | Request reset; send 6-digit code to email. |
| `password/forgot/verify/` | POST | Verify code, return session token. |
| `password/forgot/reset/` | POST | Set new password with session token. |

### 4.2 Matching (`/api/matching/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `candidates/` | GET | Users with shared interests, no existing direct chat. |
| `match/` | GET | Best match (one user by shared interests, or solo message). |
| `invites/` | POST | Send invite to a user. |
| `invites/incoming/` | GET | List received invites. |
| `invites/outgoing/` | GET | List sent invites. |
| `invites/<id>/accept/` | POST | Accept invite (can create direct chat). |
| `invites/<id>/reject/` | POST | Reject invite. |

### 4.3 Chats (`/api/chats/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `select/` | POST | Create or get chat: `{ "mode": "ai" }` or `{ "mode": "person", "peer_id": <id> }`. |
| (root) | GET | List current user’s chats. |
| `<chat_id>/` | GET | Chat detail with messages. |
| `<chat_id>/messages/` | POST | Send a message (text; supports AI commands in body). |

---

## 5. Environment Variables (.env)

All configuration is read via **environs** from a `.env` file in the backend root. Copy `.env.example` to `.env` and fill in your values.

### 5.1 Django

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (required). |
| `DEBUG` | `True` / `False`. |
| `ALLOWED_HOSTS` | Comma-separated hosts (e.g. `localhost,127.0.0.1`). |

### 5.2 PostgreSQL

| Variable | Description |
|----------|-------------|
| `DB_NAME` | Database name. |
| `DB_USER` | Database user. |
| `DB_PASSWORD` | Database password. |
| `DB_HOST` | Host (default: `localhost`). |
| `DB_PORT` | Port (default: `5432`). |

### 5.3 OpenAI (optional)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key. If missing, AI tutor uses built-in fallback. |
| `OPENAI_MODEL` | Model name (default: `gpt-4o-mini`). |

### 5.4 Email (Gmail SMTP)

| Variable | Description |
|----------|-------------|
| `EMAIL_HOST` | e.g. `smtp.gmail.com`. |
| `EMAIL_PORT` | e.g. `587`. |
| `EMAIL_HOST_USER` | Gmail address. |
| `EMAIL_HOST_PASSWORD` | App password (not account password). |
| `EMAIL_USE_TLS` | `True`. |
| `DEFAULT_FROM_EMAIL` | Sender address (often same as `EMAIL_HOST_USER`). |

---

## 6. Database Models (Brief)

### 6.1 User app

- **User** — Custom user (extends AbstractUser): username, email, password, first_name, last_name, bio, is_active.
- **InterestOption** — Named interest (e.g. "Python", "Math").
- **Interest** — User ↔ InterestOption (many-to-many via model).
- **EmailVerificationCode** — Email, 6-digit code, session_token, expires_at; for registration and forgot-password.

### 6.2 Matching app

- **ChatInvite** — from_user, to_user, status (pending/accepted/rejected), created_at.

### 6.3 Chats app

- **Chat** — kind (ai / direct), user_a, user_b (null for AI), pair_key, current_topic, current_task, current_task_hint, last_command.
- **ChatMessage** — chat, sender_type (user / ai), sender_user (null for AI), content, command.
- **AIAttempt** — chat, task_text, answer_text, score, feedback (for #answer evaluations).
- **ChatTopic** — chat, topic_name, normalized_name (history of topics per chat).

---

## 7. AI Features (Chat Tutor)

The chat service (`chats/services.py`) supports:

- **#topic** [optional custom topic] — Set or generate a learning topic (uses interests and history).
- **#task** — Generate a task for the current topic.
- **#hint** — Get a hint for the current task.
- **#answer &lt;text&gt;** — Submit an answer; AI evaluates and returns score + feedback; stored in `AIAttempt`.
- **#evaluate** — Return progress summary (attempts, average/best score, current topic).

In **AI chats**, any user message can get an AI reply (topic/task/hint/evaluation or free-form reply). In **direct (person) chats**, only messages that start with a command trigger an AI response; plain messages are stored as user messages only.

- **OpenAI**: topic generation, task, hint, evaluation, chat reply, progress summary (JSON mode).
- **Fallback**: rule-based topic/task/hint, simple scoring and feedback, and short instructional reply if OpenAI is unavailable or not configured.

---

## 8. Main Backend Tasks (What It Does)

1. **Auth** — Registration (4 steps with email verification), login (JWT), logout (refresh blacklist), profile, password change, forgot-password (3 steps).
2. **Users & interests** — Custom user model, interest options, and user–interest links for matching.
3. **Matching** — Best match and candidates by shared interests; send/accept/reject invites.
4. **Chats** — Create/list AI and direct chats; send messages; parse commands and call tutor (OpenAI or fallback); persist messages and attempts.
5. **Email** — Send 6-digit codes for registration and password reset via SMTP (Gmail).
6. **API docs** — OpenAPI schema and Swagger/ReDoc UI.

---

## 9. Run & Deploy (Backend Only)

### 9.1 Install dependencies (Poetry)

```bash
cd backend
poetry install
```

### 9.2 Environment

Copy `.env.example` to `.env` and set SECRET_KEY, DB_*, EMAIL_*, and optionally OPENAI_API_KEY.

### 9.3 Database

```bash
poetry run python manage.py migrate
poetry run python manage.py createsuperuser   # optional, for admin
```

### 9.4 Run dev server

```bash
poetry run python manage.py runserver
```

- API: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/api/schema/swagger-ui/`
- Admin: `http://127.0.0.1:8000/admin/`

For production, use a proper WSGI/ASGI server (e.g. Gunicorn/uWSGI + Nginx) and set DEBUG=False and correct ALLOWED_HOSTS.

---

*This document describes only the backend: libraries, tools, APIs, database, AI integration, and configuration. Frontend details are in the frontend documentation.*
