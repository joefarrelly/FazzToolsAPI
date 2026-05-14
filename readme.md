# FazzToolsAPI

Django REST Framework backend for **FazzTools** — a World of Warcraft companion app.

Syncs character data (professions, equipment, mounts, pets) from the Blizzard Battle.net API and parses WoW Lua addon exports to serve keybind data.

The companion frontend lives at [FazzToolsFrontend](../FazzToolsFrontend).

## Stack

- Python 3.12, Django 5.2, Django REST Framework 3.15.2
- MySQL 8, Redis 7
- Celery 5 (async tasks)
- Docker Compose

## Getting started

**1. Clone and configure**

```bash
cp .env.example .env
# Fill in your values — see .env.example for descriptions
```

**2. Start with Docker**

```bash
docker compose up
```

This starts four services: `web` (Django on port 8000), `worker` (Celery), `db` (MySQL on 3306), `redis` (on 6379).

**3. Run migrations**

```bash
docker compose exec web python manage.py migrate
```

## Environment variables

See `.env.example` for the full list. Key ones:

| Variable | Description |
|----------|-------------|
| `FRONTEND_URL` | Frontend origin for CORS — `http://localhost:3000` in dev |
| `BLIZZ_CLIENT` | Blizzard OAuth app client ID |
| `BLIZZ_SECRET` | Blizzard OAuth app secret |
| `BLIZZ_REDIRECT_URI` | Must exactly match the redirect URI used by the frontend OAuth flow |
| `HASH_KEY` | Secret used to HMAC-hash the Blizzard user ID |
| `DATA_PASSWORD` | Password to trigger a full data scan |

> After changing `.env`, run `docker compose up -d web` rather than `docker compose restart` — `restart` does not re-read env files.

## API overview

| Prefix | Description |
|--------|-------------|
| `POST /api/custom/bnetlogin/` | Battle.net OAuth2 callback — logs in / creates user |
| `POST /api/custom/scanalt/` | Triggers async alt scan for a user |
| `POST /api/custom/datascan/` | Triggers async static data scan (password-protected) |
| `/api/profile/` | User profile data (alts, professions, equipment, mounts, pets) |
| `/api/data/` | Static WoW game data |

## Branch flow

```
feature branches → dev → main
```
