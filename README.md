# FishClaim UI (Vite + React)

Frontend for FishClaim. Consumes the FastAPI backend.

## Setup
- `npm install`
- Copy `.env.local.example` to `.env.local` and set `VITE_API_BASE_URL` (e.g. `http://localhost:8080/api` for local API).
- Dev: `npm run dev` (default port 5173)
- Lint/tests (if configured later): `npm run lint`, `npm test`

## Day-to-day workflow (with backend)
- Start from `dev` in both repos; create the same feature branch name (e.g. `feature/auth-session-hardening`).
- Run the backend locally; point `VITE_API_BASE_URL` to it. Keep secrets out of git.
- Keep commits small and focused; backend and frontend commits can be separate but branches should match.
- Run checks before pushing (backend `pytest`; here `npm run lint`/tests if present).
- Push both branches to origin when the end-to-end slice works; open PRs to `dev`.
- Promote `dev` → `main` via PRs only; no direct pushes to `main`.
