FishClaim — Multiplayer Fishing Territory Game

A map-based fishing claim game where players can claim river zones, log catches, and compete for territory in a persistent world.
This project includes:

FastAPI backend (Dockerized, running on Ubuntu + PostGIS)

React + Vite frontend

MapLibre map rendering (watersheds, river zones, claims)

JWT authentication

Territory & claim mechanics

Docker deployment + NGINX staging UI



---


Features (Implemented So Far)

✔ Backend (FastAPI)

JWT authentication (login + register)

Waters & zones API (/api/waters, /api/waters/{id}/zones)

Claim system:

Get claims by zone

Place new claim (replaces weaker claim)


Catches log endpoint

Swagger docs available at /api/docs

Dockerized (FastAPI + Uvicorn + PostGIS)


✔ Frontend (React + Vite)

Login flow using JWT

Token stored & attached to Axios

Water selection sidebar

MapLibre map with:

Watersheds

River zones

Claims overlay


Claim placement UI + feedback modal

Error notifications

API abstraction layer


✔ DevOps / Server

Backend & database running on Ubuntu server through Portainer

Staging UI build served by NGINX proxying to backend

Environment variables supported (VITE_API_BASE_URL)

GitHub repo with:

main (protected)

dev (integration/testing)

feature branches (feature/*)




---

Tech Stack

Frontend

React (Vite + JSX)

MapLibre GL

Axios

Tailwind (optional)

Docker + NGINX (for staging)


Backend

FastAPI

PostgreSQL + PostGIS

SQLAlchemy

Pydantic Schemas

JWT Authentication


DevOps

Docker / Docker Compose

Portainer (Ubuntu server)

NGINX reverse proxy

GitHub flow branching strategy



---

Local Development Setup

1) Clone the repo

git clone https://github.com/<yourname>/fishclaim.git
cd fishclaim/ui

2) Install dependencies

npm install

3) Create .env.local

VITE_API_BASE_URL=http://10.100.1.37:8080/api
MAP_STYLE=https://demotiles.maplibre.org/style.json

4) Run Vite dev server

npm run dev -- --host

Your UI will be available at:

http://localhost:5173
http://<PC-LAN-IP>:5173 (for testing on your phone)


---

Running the Backend (Docker)

Backend & PostGIS run via Portainer on your server:

API Base URL: http://10.100.1.37:8080/api

Swagger docs: http://10.100.1.37:8080/docs


If you need to rebuild:

docker compose up -d --build


---

Staging UI Deployment (Docker + NGINX)

The UI has a production build served via NGINX.
Example files included in repo:

nginx.conf

server {
  listen 80;
  root /usr/share/nginx/html;

  location / {
    try_files $uri /index.html;
  }

  location /api/ {
    proxy_pass http://10.100.1.37:8080/api/;
  }
}

Dockerfile

FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
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
