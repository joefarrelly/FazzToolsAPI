# Ship Changes as PR

Same as the global /mr skill, with one additional step before committing: run ruff checks inside Docker.

## Steps

Follow all steps from the global mr skill, but insert this step between "Stage all changes" and "Commit":

**Run ruff checks** — run `docker compose exec web ruff check .` and `docker compose exec web ruff format --check .` from the project root. If either fails, auto-fix with `docker compose exec web ruff check . --fix` and `docker compose exec web ruff format .`, then re-stage with `git add -A` before committing. If Docker is not running, skip this step and note it in the response.
