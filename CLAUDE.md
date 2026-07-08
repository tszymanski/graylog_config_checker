# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Two standalone Python CLI scripts that read data from the Graylog REST API using a per-instance API token. There is no package, no framework, and no shared module — the two scripts intentionally duplicate their `read_config` and `graylog_get` helpers.

- `graylog_config_checker.py` — reads streams, pipelines, and index sets across one or more Graylog instances; emits per-instance CSVs (`--save`) or a cross-instance stream presence matrix (`--diff`), optionally transposed (`--data-transpose`), using pandas DataFrames.
- `graylog_permission_checker.py` — reads a single user's permissions from `/api/users/{username}`; prints or saves them as `text`, `json`, or `csv`.

## Configuration

Both scripts take `--config <file>`, a YAML **list** of single-key maps (order matters — it defines column order in diff output):

```yaml
- graylog-dev:
    host: "https://graylog-dev.example.com"
    token: "your-api-token"
```

API auth uses the token as the username with the literal password `"token"` (`requests` basic auth: `(token, "token")`). Any HTTP error calls `raise SystemExit(err)` — scripts abort on the first failed request.

`config.yaml`, `tests/config.yaml`, and `tests/.env` hold real secrets/tokens and are gitignored. Never commit them.

## Lint / CI

Lint is the only automated check (there is no unit test suite):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/flake8 .
```

`.flake8` sets max-line-length 120 and excludes the venvs and `temp_graylog_env`. CI (`.github/workflows/docker-build-push.yml`) runs hadolint + flake8, then builds and pushes the image to `ghcr.io` and Trivy-scans it. Match the flake8 config before assuming a change is clean.

## Docker

The image entrypoint is `graylog_config_checker.py`; run the permission checker via `--entrypoint /code/graylog_permission_checker.py`. Working dir is `/code`. Mount config read-only and an output dir:

```bash
docker build -t graylog_config_checker .
docker run -it --rm -v $(pwd)/config.yaml:/code/config.yaml:ro -v $(pwd)/output:/code/output \
    graylog_config_checker --config config.yaml --save --file-prefix output/streams
```

Keep the `FROM python:alpine<version>` base pinned to a **currently-supported** Alpine tag. An EOL Alpine stops receiving security patches, so its packages accrue CVEs that Trivy (and the CI scan) will flag as HIGH/CRITICAL even though nothing in our code changed. Bumping the base tag is the fix; verify with `trivy image graylog_config_checker:latest`.

## Local test environment (`tests/`)

A full Graylog stack (MongoDB + DataNode + Graylog) via `tests/docker-compose.yml`, driven by `tests/Makefile`, for exercising the scripts against a real API. Run all `make` targets from inside `tests/`.

First-time setup requires a manual browser preflight wizard — Graylog prints a **random** admin password to its logs on first boot that is *not* `GRAYLOG_ROOT_PASSWORD` from `tests/.env` (that only activates after the wizard finishes). See README.md "Local Test Environment" for the full flow. Typical loop:

```bash
cd tests
make setup && make start      # then complete the preflight wizard in the browser once
make create-token             # writes tests/config.yaml with an admin API token
make seed                     # tests/seed_data.py: random streams + users with mixed roles
make run                      # runs both scripts against the local instance
make clean                    # tear down and wipe volumes (resets preflight state)
```

`make run` uses the local `.venv`; `make run-image` runs the same via the Docker image with `--network host`. DataNode needs `vm.max_map_count=262144` (`make sysctl`, needs sudo).

`temp_graylog_env/` is a vendored clone of Graylog's official docker-compose repo, kept for reference only — not used by the scripts or the test Makefile.

## Conventions

- Python 3, 4-space indent, PEP8 (enforced by flake8). Match the existing procedural style.
- Every request goes through the local `graylog_get` helper; keep that pattern rather than calling `requests` directly.
- Scripts are executable (`#!/usr/bin/env python`) and carry `__version__` / `__author__` dunders — keep these in sync with the Dockerfile's `org.opencontainers.image.version` label when bumping the version.
