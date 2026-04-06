# Xahive Compliance Checklist (MVP)

Modular compliance readiness checklist (NIST CSF 2.0 first) with per-question checklist criteria, attestation, and status.

## What you get in this MVP
- **Static UI**: HTML + vanilla JS checklist experience.
- **API**: FastAPI serves module metadata and question lists from JSON packs on disk (`GET /api/modules`, `GET /api/modules/{id}/items`).
- **Storage**:
  - **Browser `localStorage` only** for session id, a client-generated secret, and per-item responses (no server database).

## Local dev (Docker Compose)
From this folder:

```bash
docker compose up --build
```

Then open:
- UI: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

## Notes
- The NIST CSF 2.0 module content is generated from the provided PDF into a module pack under `backend/modules/`.
