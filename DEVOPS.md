# DevOps Runbook

## Contributing workflow

All changes must go through a pull request:

1. Create a branch from `main`:
   ```bash
   git checkout -b your-feature-or-fix
   ```
2. Push the branch and open a pull request against `main`.
3. GitHub Actions CI must pass (linting, tests) before the PR can be merged.
4. Merge only after CI is green — do not push directly to `main`.

---

## Deployment models

There are two distinct deployment models in this repo.

| Service | Model | Image source |
|---------|-------|--------------|
| prince-archiver | Image tag + `docker compose pull` | Docker Hub (CI-published on tag push) |
| surf-archiver | Image tag + `docker compose pull` | Docker Hub (CI-published on tag push) |
| export-ingester | `git pull` + container restart | Local build only — no registry |

---

## Model A — prince-archiver & surf-archiver

### Release a new version

Push a semver tag with the service prefix to trigger the GitHub Actions build:

```bash
git tag prince-archiver/v1.2.3
git push origin prince-archiver/v1.2.3
# or
git tag surf-archiver/v1.2.3
git push origin surf-archiver/v1.2.3
```

GitHub Actions builds the image and pushes it to Docker Hub automatically.

### Deploy on the production host

```bash
# Update TAG in .env
sed -i 's/TAG=.*/TAG=v1.2.3/' .env

# Pull the new image and recreate containers
docker compose -f compose.yml -f compose.prod.yml pull
docker compose -f compose.yml -f compose.prod.yml up -d

# Verify
docker compose -f compose.yml -f compose.prod.yml ps
docker compose -f compose.yml -f compose.prod.yml logs --tail=50 state-manager
```

### Rollback

```bash
sed -i 's/TAG=.*/TAG=v1.2.2/' .env
docker compose -f compose.yml -f compose.prod.yml pull
docker compose -f compose.yml -f compose.prod.yml up -d
```

---

## Updating the surf-archiver CLI

The `surf-archiver-cli` is a separate Python package installed directly on the SURF Data
Archive machine via [pipx](https://github.com/pypa/pipx). It is distinct from the
`surf-archiver-remote` Docker image (the ARQ worker that SSHes into the archive machine).

### 1. Bump the version

Edit `surf-archiver/pyproject.toml` and increment the `version` field:

```toml
[tool.poetry]
name = "surf-archiver"
version = "0.1.3"   # <- bump this
```

### 2. Build the wheel

```bash
cd surf-archiver
poetry build
# Produces dist/surf_archiver-<version>-py3-none-any.whl
```

### 3. Copy the wheel to the SURF Data Archive

```bash
scp dist/surf_archiver-<version>-py3-none-any.whl <user>@<surf-host>:~/
```

### 4. Reinstall on the SURF Data Archive

```bash
ssh <user>@<surf-host>

# Force-reinstall from the new wheel
pipx install --force ~/surf_archiver-<version>-py3-none-any.whl

# Verify
surf-archiver-cli --help
surf-archiver-cli now
```

### 5. Clean up

```bash
rm ~/surf_archiver-<version>-py3-none-any.whl
```

---

## Model B — export-ingester

The export-ingester has no published image. The compose file mounts the source directory
into the container (`./export_ingester:/app/export_ingester`), so the running code is the
files on disk. Updating is a pull + restart.

### Deploy a code change

```bash
# On the production host, inside the repo directory
git pull origin main

# Restart so ARQ picks up the updated Python files
docker compose -f compose.yml restart export-ingester

# Verify cron jobs are registered
docker compose -f compose.yml logs --tail=30 export-ingester
```

### Rebuild the image

Only needed when `pyproject.toml` or other non-mounted files change (e.g. new dependency):

```bash
docker compose -f compose.yml build export-ingester
docker compose -f compose.yml up -d export-ingester
```

### Rollback

```bash
git checkout <previous-commit>
docker compose -f compose.yml restart export-ingester
```

---

## Database migrations (prince-archiver)

Migrations are run automatically by the `prestart` service on every `docker compose up`.
To run manually:

```bash
docker compose -f compose.yml -f compose.prod.yml run --rm prestart
```

---

## Viewing logs

### Live on the host

```bash
# prince-archiver workers
docker compose -f compose.yml -f compose.prod.yml logs -f exporter purger

# state-manager API
docker compose -f compose.yml -f compose.prod.yml logs -f state-manager

# export-ingester
docker compose -f compose.yml logs -f export-ingester

# surf-archiver
docker compose -f compose.yml -f compose.prod.yml logs -f surf-archiver-remote
```

### In Grafana Cloud (Loki)

Logs are shipped via Grafana Alloy. Containers must have the `logging: loki` label (set
in `compose.prod.yml`) to be picked up.

Useful Loki queries:

```
# All errors across prince-archiver
{job="prince-archiver-prod"} | level="error"

# A specific module
{logger="prince_archiver.entrypoints.purger.functions"}

# Surf-archiver staging
{job="prince-archiver-staging"}
```

---

## Checking worker health

ARQ workers expose a health check key in Redis (`arq:health:<worker>`), updated every
5 minutes. Docker reads it via the `healthcheck` stanza in `compose.yml`.

```bash
# Container-level health status
docker compose -f compose.yml -f compose.prod.yml ps

# Manually run the ARQ health check for a specific worker
docker compose -f compose.yml -f compose.prod.yml exec exporter \
  python -m arq prince_archiver.entrypoints.exporter.WorkerSettings --check

docker compose -f compose.yml -f compose.prod.yml exec purger \
  python -m arq prince_archiver.entrypoints.purger.WorkerSettings --check
```

---

## Restarting a single service

```bash
docker compose -f compose.yml -f compose.prod.yml restart exporter
```

---

## Resource inspection

```bash
# Live CPU/memory per container
docker stats

# Environment variables inside a running container
docker compose -f compose.yml -f compose.prod.yml exec exporter env
```

---

## PostgreSQL backup

Uses the `aws-cli` service (requires `--profile tools`):

```bash
docker compose -f compose.yml -f compose.prod.yml \
  --profile tools run --rm aws-cli \
  s3 cp /aws/backup.dump s3://<bucket>/backups/$(date +%F).dump
```

---

## Infrastructure services

The monitoring and routing stack lives in `infrastructure/` and is managed separately.

| Component | Directory | Purpose |
|-----------|-----------|---------|
| Grafana Alloy | `infrastructure/alloy/` | Ships logs (Loki) and metrics (Prometheus) to Grafana Cloud |
| Redis | `infrastructure/redis/` | Shared Redis with RDB persistence and S3 backup |
| Traefik | `infrastructure/traefik/` | Reverse proxy for the state-manager API |

Each has its own `compose.yml`. Start them with:

```bash
cd infrastructure/alloy && docker compose up -d
cd infrastructure/redis && docker compose up -d
cd infrastructure/traefik && docker compose up -d
```

Alloy requires `PROM_USERNAME`, `LOKI_USERNAME`, and `GRAFANA_API_TOKEN` in its `.env`.
