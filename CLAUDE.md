# FazzToolsAPI

Django REST Framework backend for **FazzTools** — a World of Warcraft companion app. Integrates with the Blizzard Battle.net API to sync character data (professions, equipment, mounts, pets) and stores uploaded WoW Lua addon exports for future addon-only data (gold, currencies, lockouts).

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
```

After changing `.env`, use `docker compose up -d web` (not `restart`) to pick up the new values.

## Branch flow

`feature branches` → `dev` → `main`

## Project layout

```
backend/                Django project config (settings, urls, celery, wsgi)
  test_settings.py      Overrides DB→SQLite and cache→locmem for pytest
apicore/                The single Django app
  models.py             All DB models
  views.py              All ViewSets + Lua file parser
  tasks.py              Celery tasks (fullAltScan, fullDataScan)
  serializers.py        DRF serializers
  permissions.py        IsSessionUser permission class
  libs/
    lua_parser.py         Hand-rolled Lua-table-to-JSON converter
    icon_mapping.py       Mount/pet icon mappings
    faction_expansion.py  Hardcoded faction_id → expansion name mapping (283 factions)
    expansion_order.py    tier_sort_key — sorts profession tiers by expansion order
  migrations/           DB migrations
tests/                  pytest suite (33 tests); run via pytest tests/
conftest.py             pytest env-var setup (pytest_configure hook)
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
- `altachievements` — `ProfileAltAchievement`: Achievement completions per alt
- `altreputations` — `ProfileAltReputation`: Faction standing per alt
- `altmythicplus` — `ProfileAltMythicPlus`: Current-season M+ rating summary per alt
- `altmythicplusdungeons` — `ProfileAltMythicPlusDungeon`: Best run per dungeon per alt
- `altaddondata` — `ProfileAltAddonData`: Gold + played time per alt, parsed from the uploaded `.lua` file (addon-only, no Blizzard API equivalent)

### Data endpoints (static WoW data, synced via DataScan task)
- `professions`, `professiontiers`, `professionrecipes`, `reagents`, `recipereagents`
- `equipments`, `equipmentvariants`
- `mounts`, `pets`
- `achievements` — `DataAchievement`: All WoW achievements (name, points, category)
- `factions` — `DataFaction`: All WoW reputation factions
- `mythicdungeons` — `DataMythicDungeon`: All Mythic+ dungeons (current and historical)

### Custom endpoints
- `POST /api/custom/bnetlogin/` — Battle.net OAuth2 callback; creates/updates user and syncs alts
- `POST /api/custom/logout/` — Flushes Django session and removes auth state
- `POST /api/custom/scanalt/` — Triggers `fullAltScan` Celery task for a user
- `POST /api/custom/datascan/` — Triggers all data scans (Django admin required)
- `POST /api/custom/datascan/professions/` — Triggers profession data scan only
- `POST /api/custom/datascan/mounts/` — Triggers mount data scan only
- `POST /api/custom/datascan/pets/` — Triggers pet data scan only
- `POST /api/custom/datascan/achievements/` — Triggers achievement data scan only
- `POST /api/custom/datascan/factions/` — Triggers faction data scan only
- `POST /api/custom/datascan/mythicdungeons/` — Triggers Mythic+ dungeon catalog scan only

## Key data flows

### Battle.net login
`BnetLogin.create` → exchanges auth code for token (using `Authorization: Bearer` header) → fetches WoW profile → HMAC-hashes Blizzard user ID → upserts `ProfileUser` and all `ProfileAlt` records.

### Alt scan (`fullAltScan` Celery task)
Dispatches two sets of tasks in parallel:

**Per-alt** (`scan_single_alt` × N alts):
1. Character summary → updates `ProfileAlt.alt_ilvl` (equipped item level)
2. `/professions` → upserts `ProfileAltProfession` + `ProfileAltProfessionData`
3. `/equipment` → upserts `ProfileAltEquipment` + `DataEquipment` / `DataEquipmentVariant`
4. `/reputations` → upserts `ProfileAltReputation` per faction
5. `/mythic-keystone-profile` → upserts `ProfileAltMythicPlus` + `ProfileAltMythicPlusDungeon`. The main endpoint only lists season refs (no rating/runs) — the season id isn't flagged as "current" anywhere, so `max(season.id)` is used to pick it, then a second call to `/mythic-keystone-profile/season/{id}` fetches `mythic_rating` and `best_runs`. Blizzard can list two `best_runs` entries per dungeon (best-timed and best-overall, same `map_rating` but different `keystone_level`) — the sync keeps the higher level.

**Per-user** (`scan_user_collection` × 1):
Picks the highest-level, highest-ilvl alt per faction (Alliance + Horde) and fetches:
- `/collections/mounts` → links known `DataMount` to user via `ProfileUserMount`
- `/collections/pets` → links known `DataPet` to user via `ProfileUserPet`
- `/achievements` → upserts `ProfileAltAchievement` for that representative alt

### Data scan (`fullDataScan` Celery task)
Dispatches six independent subtasks: `scanProfessionData`, `scanMountData`, `scanPetData`, `scanAchievementData`, `scanFactionData`, `scanMythicDungeonData`. Each can also be triggered individually via its own endpoint. The dungeon index requires `namespace=dynamic-eu` (not `static-eu` like other catalogs).

### Scheduled tasks (`CELERY_BEAT_SCHEDULE` in `settings.py`)
- `purge_stale_profiles` — daily, deletes expired profile records.
- `fullDataScan` — weekly, Sunday 03:00 UTC, with `BLIZZ_CLIENT`/`BLIZZ_SECRET` baked into the schedule args at startup. The admin-triggered `/api/custom/datascan/` endpoints still work for ad-hoc/manual scans (e.g. testing a single category).

### Lua addon file
`ProfileUser.perform_update` validates and stores a `FazzToolsScraper.lua` addon export, then parses it via `LuaParser` and upserts `ProfileAltAddonData` for each alt found in the file (matched by `f"{alt.alt_name}-{alt.alt_realm}"`, the display name + display realm key `core.lua` writes). This is parse-on-upload, not parse-on-read — there's no Celery sync task for this data since it only ever exists in the addon export, never the Blizzard API, so the upload itself is the sync point. A failed parse logs a warning and leaves the stored file/timestamp update intact rather than failing the upload. Currencies/lockouts/keystone/vault are captured by the addon but not yet parsed into a model — same pattern, not built.

## Database tables (all prefixed `ft_`)

**Data (static):** `ft_data_profession`, `ft_data_professiontier`, `ft_data_professionrecipe`, `ft_data_reagent`, `ft_data_recipereagent`, `ft_data_equipment`, `ft_data_equipmentvariant`, `ft_data_mount`, `ft_data_pet`, `ft_data_achievement`, `ft_data_faction`, `ft_data_mythicdungeon`

**Profile (user):** `ft_profile_user`, `ft_profile_alt`, `ft_profile_altprofession`, `ft_profile_altprofessiondata`, `ft_profile_altequipment`, `ft_profile_usermount`, `ft_profile_userpet`, `ft_profile_altachievement`, `ft_profile_altreputation`, `ft_profile_altmythicplus`, `ft_profile_altmythicplusdungeon`, `ft_profile_altaddondata`

## Things to know

- All Blizzard API calls target the **EU** region (`eu.battle.net`, `eu.api.blizzard.com`)
- Blizzard API authentication uses `Authorization: Bearer <token>` header (query param method was deprecated)
- `BLIZZ_REDIRECT_URI` must exactly match what the frontend sends in the initial OAuth request — mismatch causes a 400 from Blizzard's token endpoint
- Equipment variants use a composite `variantCode` built from the item's `bonus_list` IDs concatenated as a string
- The Lua parser (`recursive()` in views.py) uses two module-level globals (`all_lines`, `index_count`) — it's not thread-safe but works under Celery
- Several views use a flexible `fields[]` query param pattern to let the frontend request only the columns it needs
- `ProfileAltEquipment` stores equipment as `"equipmentId:variantCode"` strings rather than FK relations
- Expiry dates (`altExpiryDate`, `altProfessionExpiryDate`, etc.) are set to `now + 30 days` on each scan but are not actively enforced server-side
- `DataScan` requires a Django admin user (`IsAdminUser`) — not the session-based auth used by profile endpoints
- Session auth: `BnetLogin` sets `request.session["user_id"]` on login; profile views enforce it via `IsSessionUser` (checks session against `?user=` param). `CORS_ALLOW_CREDENTIALS = True` is required for cookies to flow cross-origin.
