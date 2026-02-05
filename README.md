# IIIF Presentation API

FastAPI service for storing and serving IIIF Presentation 3 manifests for CRKN. Manifests are uploaded as JSON, written to OpenStack Swift, and retrieved by manifest ID. Upload is protected (Azure AD or JWT); retrieval is public. This API backs the CRKN Digirati editor.

Example flow:

1. Upload `manifest.json` via `PUT /file` (Azure AD) or `PUT /admin/file` (JWT).
2. Retrieve it via `GET /manifest/{manifest_id}`.
3. Render in Mirador.

## Table of Contents

1. [Quick Start (Docker, recommended)](#quick-start-docker-recommended)
2. [Docker Desktop + WSL2 (Windows + Ubuntu)](#docker-desktop--wsl2-windows--ubuntu)
3. [Quick Start (Local Python)](#quick-start-local-python)
4. [Configuration and Secrets (.env)](#configuration-and-secrets-env)
5. [API Basics](#api-basics)
6. [IIIF in 2 Minutes](#iiif-in-2-minutes)
7. [FastAPI in 2 Minutes](#fastapi-in-2-minutes)
8. [Project Map](#project-map)
9. [Swift Notes](#swift-notes)
10. [Development](#development)

## Quick Start (Docker, recommended)

1. Install Docker Desktop.
2. Create a `.env` file in the repo root (see Configuration and Secrets below).
3. Build and run:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000` and docs at `http://localhost:8000/docs`.

Try it (requires a manifest already in Swift):

```bash
curl "http://localhost:8000/manifest/<manifest_id>"
```

## Docker Desktop + WSL2 (Windows + Ubuntu)

These steps set up Docker Desktop to build containers in Ubuntu on WSL2.

1. Install Docker Desktop (Windows).
2. Ensure Docker Desktop uses the WSL2 engine: Docker Desktop -> Settings -> General -> check Use the WSL 2 based engine.
3. Install WSL + Ubuntu in PowerShell (Admin):

```powershell
wsl --install -d Ubuntu
```

4. Reboot if prompted.
5. Launch Ubuntu from the Start menu or run `wsl`.
6. Update Ubuntu packages:

```bash
sudo apt update
sudo apt upgrade -y
```

7. In Ubuntu, navigate to the repo and build:

```bash
cd /mnt/c/Users/<you>/Documents/github/crkn-IIIF-presentation-api
docker compose build
```

## Quick Start (Local Python)

1. Install Python 3.12 (matches `pyproject.toml`).
2. Create and activate a virtual environment.
3. Install dependencies.
4. Create `.env` and fill in values.
5. Start the server.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

If you are on Windows PowerShell, activation looks like this:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Configuration and Secrets (.env)

`.env` is required for local development and Docker. This repo includes a sample `.env`; treat it as a template and avoid committing real secrets.

Required for startup:

- `SWIFT_AUTH_URL` - Swift auth URL (example: `https://swift.example.com/auth/v1.0`).
- `SWIFT_USER` - Swift username.
- `SWIFT_KEY` - Swift key/password.
- `CONTAINER_NAME` - Swift container where manifests are stored.

Required for `/admin/file`:

- `EDITOR_SECRET_KEY` - Secret used to sign JWTs (HS256).

Required for `/file` (Azure AD):

- `OPENAPI_CLIENT_ID`
- `APP_CLIENT_ID`
- `TENANT_ID`
- `SCOPE_DESCRIPTION` (defaults to `user_impersonation` if unset)

Optional:

- `AZURE_AUTH_ENABLED` - Set to `false` to skip OpenID discovery on startup.
- `BACKEND_CORS_ORIGINS` - Comma-separated list for CORS.
- `SWIFT_PREAUTH_URL` - Pre-auth URL (used by the Swift client helper, not by the HTTP flow).
- `REDIS_URL` - Redis connection string 

Important:

- The API authenticates to Swift on startup and will fail fast if credentials are invalid.
- Upload endpoints require a valid JWT or Azure AD token.
- For local development without Azure AD, use `/admin/file` with a JWT signed by `EDITOR_SECRET_KEY`.

## API Basics

Base URL: `http://localhost:8000`

Endpoints:

- `GET /` - Redirects to docs.
- `GET /manifest/{manifest_id}` - Fetch a manifest by ID.
- `PUT /file` - Upload a manifest (Azure AD token required).
- `PUT /admin/file` - Upload a manifest (JWT required).

`manifest_id` is the last two path segments of the manifest `id` field. For example, if the manifest `id` is `https://example.org/iiif/foo/bar/manifest.json`, the stored object is `foo/bar/manifest.json` and the retrieval URL is `/manifest/foo/bar`.

Example requests:

```bash
curl "http://localhost:8000/manifest/<collection>/<id>"
```

```bash
curl -X PUT "http://localhost:8000/admin/file" \
  -H "Authorization: Bearer <jwt>" \
  -F "file=@manifest.json;type=application/json"
```

```bash
curl -X PUT "http://localhost:8000/file" \
  -H "Authorization: Bearer <azure_ad_token>" \
  -F "file=@manifest.json;type=application/json"
```

API docs:

- Local OpenAPI docs at `http://localhost:8000/docs`.

## IIIF in 2 Minutes

IIIF (International Image Interoperability Framework) defines shared APIs for describing and delivering digital objects. The Presentation API 3.0 specifies the manifest format used to describe a compound object, its metadata, and the sequence of canvases.

- Presentation API spec: https://iiif.io/api/presentation/3.0/
- We use the Mirador viewer to render manifests for users.

This service expects manifests to follow Presentation 3.0. A validator is available in `utils/validator.py`; validation can be re-enabled in `utils/upload_manifest.py` if needed.

## FastAPI in 2 Minutes

Common commands:

- `uvicorn main:app --reload` - Start the dev server with reload.
- `uvicorn main:app --host 0.0.0.0 --port 8000` - Start the server for Docker-like use.
- `python -m pytest` - Run tests (if any).

## Project Map

Key files and folders:

- `main.py` - FastAPI app entrypoint and router registration.
- `api/manifest.py` - Manifest upload and retrieval endpoints.
- `utils/upload_manifest.py` - Upload and Swift write logic.
- `utils/get_manifest_conn.py` - Swift read logic.
- `utils/lifespan_handler.py` - Startup auth and token refresh.
- `Azure_auth/` - Azure AD auth configuration and JWT helper.
- `swift_config/` - Swift client connection helper.
- `utils/schema/` - Presentation API schema validation helpers.
- `load_testing/` - Locust load test scripts.

## Swift Notes

This service uses OpenStack Swift as object storage.

- On startup, the app authenticates using `SWIFT_AUTH_URL`, `SWIFT_USER`, and `SWIFT_KEY` and stores `X-Auth-Token` and `X-Storage-Url` for subsequent requests.
- Manifests are stored as `<manifest_id>/manifest.json` within the `CONTAINER_NAME` container.
- The API does not create containers; ensure the container exists and is writable by the Swift credentials.

## Development

Run container:

```bash
docker compose up
```

Run tests:

```bash
python -m pytest
```

Load testing scripts are in `load_testing/`.
