FishClaim Frontend (React + Vite)
=================================

Map-based UI for FishClaim. Talks to the FastAPI backend (`/api`).

## Stack
- React + Vite
- Axios for API calls
- MapLibre + Leaflet layers

## Dev setup
```bash
cd /home/decstar714/workspace/projects/fishclaim/frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8080/api" > .env.local  # adjust port/host
npm run dev -- --host --port 5173
# open http://localhost:5173
```

## Build
```bash
npm run build
npm run preview   # optional local preview of production build
```

## Structure
- `src/main.jsx`: bootstraps app.
- `src/App.jsx`: main layout, fetches waters/zones/claims, handles auth + catch logging.
- `src/features/map/MapView`: map rendering (claims/waters); check here for map/territory logic.
- `src/routes`: route components (if expanded).
- `src/assets`: static assets.
- Styles in `src/App.css` / `src/index.css`.

## API config
- Base URL via `VITE_API_BASE_URL` (required).
- Auth token stored in localStorage under `auth_token`; attached to Axios default headers on load.
- Key endpoints used: `/waters`, `/waters/{id}/zones`, `/claims/zone/{id}`, `/auth/login`, `/catches/`.

## Map & claims (interactive)
- Map state fetched from `/api/map/state` (see `src/features/map/MapView.jsx`).
- Draws reaches as polygons (Leaflet) using `geometry_geojson`. Claimed reaches are highlighted.
- Click a reach to see details and claim it via `POST /api/claims/` (sends `X-User-Id` header; defaults to `demo-user` if none set).
- Leaderboard: `src/features/stats/ClaimLeaderboard.jsx` consumes `/api/stats/claims`.

## Notes / cleanup targets
- Keep components lean; remove unused assets as you iterate.
- If you add env vars, document them here and ensure `.env.local` reflects them.
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

Deploy

From server or Portainer:

docker compose up -d --build

Staging UI will be available at:
http://10.100.1.37:8081


---

Branching Strategy (Team Workflow)

main

Production-ready

Protected (no direct pushes)


dev

Integration branch

All features merge into dev first


feature branches

feature/map-click-claims
feature/auth-page
feature/zone-highlights

Workflow

1. Pull latest dev:

git checkout dev
git pull


2. Make feature branch:

git checkout -b feature/my-task


3. Commit + push:

git push -u origin feature/my-task


4. Open PR → base: dev


5. After testing → merge dev → main


6. Rebuild server containers for new release




---

API Endpoints Overview

Waters

GET /api/waters
GET /api/waters/{id}/zones

Claims

GET /api/claims/zone/{zone_id}
POST /api/claims

Auth

POST /api/auth/login
POST /api/auth/register

Catches

POST /api/catches


---

Roadmap

Short-Term

Better map styling (Tarkov/Zomboid rustic vibe)

Zone highlight interactions

Claim conflict animations

Catch history view

Player stats page


Mid-Term

Seasons & leaderboards

Territory decay

Friends / teams

Mobile UI pass


Long-Term

Entire US watershed tile rendering

Replay viewer

Server-side tile preprocessing

Offline cache for field fishing



---

Contributing (Your Team)

Requirements to contribute:

You must create a feature branch

PR into dev

Code review required

main is locked and protected


Simple commit style

feat(map): zone hover highlight
fix(api): null zone_id crash
chore(ui): cleanup console logs


---

License

MIT License
