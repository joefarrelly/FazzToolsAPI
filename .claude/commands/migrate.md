# Django Migrate

Run Django database migrations via Docker Compose.

## Steps

1. **Run migrations** — execute `docker compose exec web python manage.py migrate` from the project root.

2. **Report** — show the output so the user can see which migrations were applied (or confirm "No migrations to apply." if already up to date).

## Notes

- If Docker is not running or the `web` container is not up, tell the user and suggest running `docker compose up -d` first.
- If a migration fails, show the full error output and stop — do not attempt to fake success.
