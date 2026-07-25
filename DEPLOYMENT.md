# Deployment Guide

This covers deploying Vikrm to a real server. For local development,
see the main [README.md](./README.md) instead.

## Option A: Docker Compose on a VM (DigitalOcean, AWS EC2, Azure VM, any Linux host)

The most direct path — one host running everything via
`docker-compose.prod.yml`.

**Requirements**: a Linux VM with Docker + Docker Compose installed,
at least 4GB RAM (more if running larger Ollama models), a domain
pointed at the VM's IP if you want HTTPS.

```bash
git clone <your-fork-of-this-repo>
cd vikrm

cp .env.prod.example .env.prod
# Edit .env.prod: set MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, and
# JWT_SECRET_KEY (generate with `openssl rand -hex 32`) at minimum.
# Set GOOGLE_CLIENT_ID/SECRET for OAuth — see docs/API.md's Google
# OAuth setup section, but add your production domain to "Authorized
# JavaScript origins" this time, not localhost.

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Apply migrations (one-time, and after every future schema change):
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Pull a model into Ollama (one-time):
docker compose -f docker-compose.prod.yml exec ollama ollama pull llama3.2
```

The app is now serving on port 80. For HTTPS, put a reverse proxy
(Caddy or another Nginx instance with Let's Encrypt via certbot) in
front of it — the simplest is swapping in
[Caddy](https://caddyserver.com/) as an additional service with
automatic HTTPS, since it needs almost no configuration for a
single-domain setup. That's a small addition to
`docker-compose.prod.yml` we haven't included here to keep the base
file focused, but it's a five-line service block if you want automatic
certificates.

**Backups**: the `vikrm_mysql_data` and `vikrm_chroma_data` Docker
volumes hold everything that matters (relational data and vectors,
respectively). Back them up with `docker run --rm -v
vikrm-prod_vikrm_mysql_data:/data -v $(pwd):/backup alpine tar czf
/backup/mysql-backup.tar.gz /data` (adjust the volume name prefix to
match your actual `docker volume ls` output) on whatever schedule
matters to you.

## Option B: Render

Render supports Docker-based web services directly from a Dockerfile.

1. Push this repo to GitHub.
2. Create a **Render Blueprint** or two separate **Web Services**:
   - Backend: point at `backend/Dockerfile.prod`, set the health check
     path to `/api/v1/health`, and add all the environment variables
     from `.env.prod.example` (Render's dashboard has an "Environment"
     tab for this — don't commit real secrets to the repo).
   - Frontend: point at `frontend/Dockerfile.prod`.
3. Add a **Render PostgreSQL or external MySQL** — Render's managed
   Postgres doesn't apply here since this project uses MySQL; use
   Render's "Private Service" MySQL option or an external managed
   MySQL (PlanetScale, AWS RDS) and set `MYSQL_HOST` to point at it.
4. Add a **Render Key Value (Redis)** instance and set `REDIS_HOST`
   accordingly.
5. Ollama needs a service with persistent disk and enough RAM for
   whatever model you run — Render's standard web services support
   persistent disks on paid plans.
6. Run `alembic upgrade head` via Render's shell/one-off job feature
   after the first deploy.

## Option C: Railway

Railway's workflow is similar to Render: point it at this repo, and
it auto-detects the Dockerfiles. Add MySQL and Redis directly from
Railway's plugin marketplace (both are one-click managed add-ons),
which is generally simpler than Render for this stack specifically.
Set `MYSQL_HOST`/`REDIS_HOST` (and the other `.env.prod.example`
variables) to whatever Railway's plugins expose in their connection
details.

## What's Different in Production (vs. local `docker-compose.yml`)

| | Development | Production |
|---|---|---|
| Backend image | Single-stage, `--reload`, runs as root | Multi-stage build, no reload, non-root user, multiple uvicorn workers |
| Frontend | Vite dev server | Static build served by Nginx, with gzip and immutable asset caching |
| Source code | Bind-mounted (live edits) | Baked into the image (immutable; redeploy to change) |
| `JWT_SECRET_KEY` default | Allowed | **Refused at startup** — the app raises `RuntimeError` and won't boot (see `Settings.validate_production_safety`) |
| Rate limiting | Same middleware, same behavior | Same — this isn't dev-only |
| Ports exposed | MySQL/Redis/Ollama all mapped to host for local debugging | Only the frontend's port 80 is exposed; everything else stays on the internal Docker network |

## Health Checks

- Backend: `GET /api/v1/health` (liveness) and `GET /api/v1/health/ready`
  (checks MySQL + Redis connectivity) — both used by the Docker
  `HEALTHCHECK` directives in `Dockerfile.prod`.
- Frontend (Nginx): a plain `GET /` check.

## Continuous Integration

`.github/workflows/ci.yml` runs on every push/PR to `main`: the full
backend test suite (138 tests as of Milestone 13, using in-memory
SQLite + `fakeredis` + the deterministic embedding provider — no live
MySQL/Redis/ChromaDB needed in CI), a `ruff` lint pass, and a frontend
type-check + production build. All three jobs run in parallel.
