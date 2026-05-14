# FazzToolsAPI

Django REST Framework backend for **FazzTools** — a World of Warcraft companion app. Integrates with the Blizzard Battle.net API to sync character data (professions, equipment, mounts, pets) and parses uploaded WoW Lua addon files to serve keybind data.

The companion frontend lives at `../FazzToolsFrontend` (React, port 3000 in dev).

## Stack

- Python 3.12, Django 5.2, Django REST Framework 3.15.2
- MySQL 8 database (via `mysqlclient`)
- Celery 5 for async tasks (Redis broker)
- `django-environ` for env var management
- Docker Compose for local development (services: `web`, `worker`, `db`, `redis`)
- CORS origin driven by `FRONTEND_URL` env var

## Running locally

### With Docker (recommended)

```bash
docker compose up           # Starts web, worker, db, redis
docker compose exec web python manage.py migrate
```

Ports exposed locally: `8000` (Django), `3306` (MySQL), `6379` (Redis).

### Without Docker

Requires a running MySQL and Redis instance, then:

```bash
python manage.py runserver          # Dev server
celery -A backend worker -l info    # Celery worker (required for scans)
```

### Environment variables

Copy `.env.example` to `.env` and fill in:

```
SECRET_KEY=
DEBUG_OPTION=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
CELERY_BROKER_URL=         # redis://redis:6379/0 with Docker
FRONTEND_URL=              # http://localhost:3000 in dev — drives CORS
HASH_KEY=                  # Used to HMAC-hash the Blizzard user ID into our userId
BLIZZ_CLIENT=              # Blizzard OAuth app client ID
BLIZZ_SECRET=              # Blizzard OAuth app secret
BLIZZ_REDIRECT_URI=        # Must exactly match the redirect URI registered in Blizzard dev portal
DATA_PASSWORD=             # Password to trigger a full data scan
```

After changing `.env`, use `docker compose up -d web` (not `restart`) to pick up the new values.

## Branch flow

`feature branches` → `dev` → `main`

## Project layout

```
backend/          Django project config (settings, urls, celery, wsgi)
apicore/          The single Django app
  models.py       All DB models
  views.py        All ViewSets + Lua file parser
  tasks.py        Celery tasks (fullAltScan, fullDataScan)
  serializers.py  DRF serializers
  libs/           Helper mappings (keybind_mapping, icon_mapping)
  migrations/     DB migrations
```

## API URL structure

| Prefix | Router | Description |
|--------|--------|-------------|
| `/api/admin/` | — | Django admin |
| `/api/profile/` | `profile` router | User-facing profile data |
| `/api/data/` | `data` router | Static WoW game data |
| `/api/custom/` | `custom` router | Special actions |

### Profile endpoints
- `users` — `ProfileUser`: Battle.net user record + Lua file upload
- `alts` — `ProfileAlt`: Characters linked to a user (synced from Blizzard)
- `altprofessions` — `ProfileAltProfession`: Per-alt primary professions
- `altprofessiondatas` — `ProfileAltProfessionData`: Known recipes per alt/profession
- `altequipments` — `ProfileAltEquipment`: Equipped gear slots per alt
- `usermounts` / `userpets` — Collected mounts/pets per user

### Data endpoints (static WoW data, synced via DataScan task)
- `professions`, `professiontiers`, `professionrecipes`, `reagents`, `recipereagents`
- `equipments`, `equipmentvariants`
- `mounts`, `pets`

### Custom endpoints
- `POST /api/custom/bnetlogin/` — Battle.net OAuth2 callback; creates/updates user and syncs alts
- `POST /api/custom/scanalt/` — Triggers `fullAltScan` Celery task for a user
- `POST /api/custom/datascan/` — Triggers `fullDataScan` Celery task (password-protected)

## Key data flows

### Battle.net login
`BnetLogin.create` → exchanges auth code for token (using `Authorization: Bearer` header) → fetches WoW profile → HMAC-hashes Blizzard user ID → upserts `ProfileUser` and all `ProfileAlt` records.

### Alt scan (`fullAltScan` Celery task)
For each alt belonging to a user, fetches from Blizzard API:
1. `/professions` → upserts `ProfileAltProfession` + `ProfileAltProfessionData` (creates missing `DataProfessionRecipe` entries on the fly)
2. `/equipment` → upserts `ProfileAltEquipment` + `DataEquipment` / `DataEquipmentVariant`
3. `/collections/mounts` → links known `DataMount` records to user via `ProfileUserMount`
4. `/collections/pets` → links known `DataPet` records to user via `ProfileUserPet`

### Data scan (`fullDataScan` Celery task)
Fetches Blizzard static data API indexes and walks all professions (tiers → categories → recipes → reagents) and all mounts/pets, creating `Data*` records.

### Lua keybind file
`ProfileUser.perform_update` validates and stores a `FazzToolsScraper.lua` addon export.  
`ProfileUserView.list` with `?page=all` or `?page=single` parses the stored Lua file using the `recursive()` function (a hand-rolled Lua-table-to-JSON converter) and joins results against `ProfileAlt` + Blizzard spell data. Returns per-spec keybind mappings.

## Database tables (all prefixed `ft_`)

**Data (static):** `ft_data_profession`, `ft_data_professiontier`, `ft_data_professionrecipe`, `ft_data_reagent`, `ft_data_recipereagent`, `ft_data_equipment`, `ft_data_equipmentvariant`, `ft_data_mount`, `ft_data_pet`

**Profile (user):** `ft_profile_user`, `ft_profile_alt`, `ft_profile_altprofession`, `ft_profile_altprofessiondata`, `ft_profile_altequipment`, `ft_profile_usermount`, `ft_profile_userpet`

## Things to know

- All Blizzard API calls target the **EU** region (`eu.battle.net`, `eu.api.blizzard.com`)
- Blizzard API authentication uses `Authorization: Bearer <token>` header (query param method was deprecated)
- `BLIZZ_REDIRECT_URI` must exactly match what the frontend sends in the initial OAuth request — mismatch causes a 400 from Blizzard's token endpoint
- Equipment variants use a composite `variantCode` built from the item's `bonus_list` IDs concatenated as a string
- The Lua parser (`recursive()` in views.py) uses two module-level globals (`all_lines`, `index_count`) — it's not thread-safe but works under Celery
- Several views use a flexible `fields[]` query param pattern to let the frontend request only the columns it needs
- `ProfileAltEquipment` stores equipment as `"equipmentId:variantCode"` strings rather than FK relations
- Expiry dates (`altExpiryDate`, `altProfessionExpiryDate`, etc.) are set to `now + 30 days` on each scan but are not actively enforced server-side
- `DataScan` is password-protected via `DATA_PASSWORD` env var — not authed via the normal auth system
