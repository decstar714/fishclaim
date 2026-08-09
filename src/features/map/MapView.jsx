import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { MapContainer, TileLayer, GeoJSON, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL;
const DEFAULT_CENTER = [40.612, -74.742];
const DEFAULT_ZOOM = 12;

export default function MapView() {
  const [mapState, setMapState] = useState({ waters: [], reaches: [] });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [selected, setSelected] = useState(null);
  const [userId, setUserId] = useState(localStorage.getItem("fc_user") || "demo-user");
  const [claimMsg, setClaimMsg] = useState(null);

  const fetchState = async () => {
    try {
      setLoading(true);
      setErr(null);
      const res = await axios.get(`${API_BASE}/map/state`);
      setMapState({
        waters: res.data?.waters || [],
        reaches: res.data?.reaches || [],
      });
    } catch (e) {
      setErr(e?.message || "Failed to load map state");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchState();
  }, []);

  const waterLookup = useMemo(() => {
    const map = {};
    (mapState.waters || []).forEach((w) => { map[w.id] = w.name; });
    return map;
  }, [mapState.waters]);

  const handleClaim = async (reachId) => {
    try {
      setClaimMsg(null);
      await axios.post(
        `${API_BASE}/claims/`,
        { reach_id: reachId, note: "Claimed from map UI" },
        { headers: { "X-User-Id": userId } }
      );
      setClaimMsg("Claim created!");
      await fetchState();
    } catch (e) {
      const status = e?.response?.status;
      const detail = e?.response?.data?.detail || e?.message;
      setClaimMsg(status === 409 ? "Reach already claimed" : detail || "Claim failed");
    }
  };

  const reachFeatures = useMemo(
    () =>
      (mapState.reaches || [])
        .filter((r) => r.geometry_geojson)
        .map((r) => ({
          type: "Feature",
          properties: r,
          geometry: r.geometry_geojson,
        })),
    [mapState.reaches]
  );

  const styleReach = (feature) => {
    const active = feature?.properties?.active_claim;
    return {
      color: active ? "#f59e0b" : "#3b82f6",
      weight: 2,
      fillOpacity: active ? 0.45 : 0.2,
      fillColor: active ? "#f59e0b" : "#60a5fa",
    };
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1rem", height: "600px" }}>
      <div style={{ height: "100%", borderRadius: 8, overflow: "hidden", border: "1px solid #1f2937" }}>
        <MapContainer center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} style={{ height: "100%", width: "100%" }}>
          <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <GeoJSON
            key={reachFeatures.length}
            data={{ type: "FeatureCollection", features: reachFeatures }}
            style={styleReach}
            onEachFeature={(feature, layer) => {
              layer.on("click", () => setSelected(feature.properties));
              layer.bindPopup(`${feature.properties.name}`);
            }}
          />
        </MapContainer>
      </div>
      <div style={{ background: "#0b1220", color: "#e5e7eb", borderRadius: 8, padding: "0.75rem", border: "1px solid #1f2937" }}>
        <div style={{ fontWeight: 600, marginBottom: "0.5rem" }}>Reaches & Claims</div>
        {loading && <div>Loading map state…</div>}
        {err && <div style={{ color: "#f87171" }}>{err}</div>}
        <div style={{ marginBottom: "0.75rem" }}>
          <label style={{ fontSize: "0.9rem" }}>
            User ID:&nbsp;
            <input
              value={userId}
              onChange={(e) => {
                setUserId(e.target.value);
                localStorage.setItem("fc_user", e.target.value || "demo-user");
              }}
              style={{ padding: "4px 6px", background: "#111827", border: "1px solid #1f2937", color: "#e5e7eb", borderRadius: 4 }}
            />
          </label>
        </div>
        {selected ? (
            <div style={{ border: "1px solid #1f2937", borderRadius: 8, padding: "0.75rem" }}>
            <div style={{ fontWeight: 600 }}>{selected.name}</div>
            <div style={{ fontSize: "0.9rem", opacity: 0.8 }}>
              Water: {waterLookup[selected.water_body_id] || selected.water_body_id}
            </div>
            {selected.active_claim ? (
              <div style={{ marginTop: "0.35rem", color: "#fbbf24" }}>
                Claimed by {selected.active_claim.user_id} (status {selected.active_claim.status})
                {selected.active_claim.expires_at ? ` until ${selected.active_claim.expires_at}` : ""}
              </div>
            ) : (
              <div style={{ marginTop: "0.35rem", opacity: 0.8 }}>No active claim</div>
            )}
            <button
              onClick={() => handleClaim(selected.id)}
              style={{
                marginTop: "0.5rem",
                padding: "0.5rem 0.75rem",
                background: "#2563eb",
                color: "#fff",
                border: "none",
                borderRadius: 6,
                cursor: "pointer",
              }}
            >
              Claim this reach
            </button>
            {claimMsg && <div style={{ marginTop: "0.4rem", fontSize: "0.9rem" }}>{claimMsg}</div>}
          </div>
        ) : (
          <div style={{ fontSize: "0.9rem", opacity: 0.8 }}>Click a reach on the map to view/claim.</div>
        )}
        <div style={{ marginTop: "0.75rem", fontSize: "0.9rem" }}>
          Total reaches: {mapState.reaches.length} | Waters: {mapState.waters.length}
        </div>
      </div>
    </div>
  );
}
