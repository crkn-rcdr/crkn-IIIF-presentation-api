# IIIF Presentation API

CRKN IIIF module

## Table of Contents

1. [Description](#description)
2. [Usage - Configuration options and additional functionality](#usage)
3. [Limitations - OS compatibility, etc.](#limitations)
4. [Development - Guide for contributing to the module](#development)

## Description

This API allows users to upload a IIIF manifest.json file to Swift containers and retrieve a manifest.json file by searching for a manifest ID.

## Usage

This module is used as the backend for the Digirati editor: https://github.com/crkn-rcdr/crkn-digirati-editor.

## Limitations

The uploaded manifest.json file must comply with the IIIF Presentation API requirements. The API includes a manifest.json validator from https://presentation-validator.iiif.io/.

## Development

The upload functionality is used only by CRKN, while the data retrieval functionality is open to the public.

### Docker Compose

This project can be run with Docker Compose using the repo root `.env` file.

Environment variables (set in `.env`):
- `SWIFT_AUTH_URL`
- `SWIFT_USER`
- `SWIFT_KEY`
- `SWIFT_PREAUTH_URL`
- `CONTAINER_NAME`
- `OPENAPI_CLIENT_ID`
- `APP_CLIENT_ID`
- `TENANT_ID`
- `EDITOR_SECRET_KEY`

1. Fill in the required values in `.env` (Swift and Azure AD settings are required for startup).
2. Build and run:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.
