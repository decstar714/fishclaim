// src/features/map/api.js
const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const R_PATH = import.meta.env.VITE_RIVERS_BBOX_PATH || "/rivers";
const C_PATH = import.meta.env.VITE_CLAIMS_BBOX_PATH || "/claims";

function qsFromBbox({ minX, minY, maxX, maxY }) {
  return new URLSearchParams({ minX, minY, maxX, maxY }).toString();
}

export async function fetchRiversByBbox(token, bbox) {
  const url = `${API_BASE}${R_PATH}?${qsFromBbox(bbox)}`;
  console.log("[API] rivers →", url);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) {
    const err = new Error(`rivers ${res.status} : ${await res.text()}`);
    err.status = res.status;
    throw err;
  }
  return res.json(); // { features: [...] } or your backend’s shape
}

export async function fetchClaimsByBbox(token, bbox) {
  const url = `${API_BASE}${C_PATH}?${qsFromBbox(bbox)}`;
  console.log("[API] claims →", url);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) {
    const err = new Error(`claims ${res.status} : ${await res.text()}`);
    err.status = res.status;
    throw err;
  }
  return res.json(); // { claims: [...] } or your backend’s shape
}
