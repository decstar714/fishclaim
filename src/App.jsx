// src/App.jsx
import { useEffect, useState } from "react";
import axios from "axios";
import {
  clearAuthToken,
  loadStoredToken,
  registerAuthInterceptor,
  setAuthToken,
} from "./auth/token";
import MapView from "./features/map/MapView"; // 👈 direct default import

const API_BASE = import.meta.env.VITE_API_BASE_URL; // keep your current var

function App() {
  const [waters, setWaters] = useState([]);
  const [zones, setZones] = useState([]);
  const [claims, setClaims] = useState([]);
  const [selectedWater, setSelectedWater] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [watersLoading, setWatersLoading] = useState(true);
  const [watersError, setWatersError] = useState("");
  const [zonesLoading, setZonesLoading] = useState(false);
  const [zonesError, setZonesError] = useState("");
  const [claimsLoading, setClaimsLoading] = useState(false);
  const [claimsError, setClaimsError] = useState("");

  // auth state
  const [token, setToken] = useState(loadStoredToken);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });

  // catch form state
  const [form, setForm] = useState({
    speciesId: "1",
    lengthCm: "",
    method: "fly",
    notes: "",
  });

  useEffect(() => {
    const ejectAuthInterceptor = registerAuthInterceptor(() => {
      setToken("");
    });

    return ejectAuthInterceptor;
  }, []);

  // Load waters on first render
  useEffect(() => {
    setWatersLoading(true);
    setWatersError("");
    axios
      .get(`${API_BASE}/waters/`)
      .then((res) => setWaters(res.data))
      .catch((err) => setWatersError("Failed to load waters."))
      .finally(() => setWatersLoading(false));
  }, []);

  const loadZones = async (water) => {
    setSelectedWater(water);
    setSelectedZone(null);
    setClaims([]);
    setZones([]);
    setZonesError("");
    setClaimsError("");
    setZonesLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/waters/${water.id}/zones`);
      setZones(res.data);
    } catch (err) {
      setZonesError("Failed to load zones.");
    }
    setZonesLoading(false);
  };

  const loadClaims = async (zone) => {
    setSelectedZone(zone);
    setClaimsError("");
    setClaimsLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/claims/zone/${zone.id}`);
      setClaims(res.data);
    } catch (err) {
      setClaimsError("Failed to load claims.");
      setClaims([]);
    }
    setClaimsLoading(false);
  };

  // 🔑 Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append("username", loginForm.username);
      params.append("password", loginForm.password);

      const res = await axios.post(`${API_BASE}/auth/login`, params, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const t = res.data.access_token;
      setToken(t);
      setAuthToken(t);
      alert("Logged in as " + loginForm.username);
    } catch (err) {
      console.error("Login failed", err);
      alert("Login failed – check username/password or backend logs.");
    }
  };

  const handleLogout = () => {
    setToken("");
    clearAuthToken();
  };

  // 🪝 Log catch
  const handleLogCatch = async (e) => {
    e.preventDefault();
    if (!token) {
      alert("You must be logged in to log a catch.");
      return;
    }
    if (!selectedWater || !selectedZone) {
      alert("Select a water and zone first.");
      return;
    }
    try {
      await axios.post(`${API_BASE}/catches/`, {
        water_id: selectedWater.id,
        zone_id: selectedZone.id,
        species_id: Number(form.speciesId),
        length_cm: Number(form.lengthCm),
        method: form.method,
        notes: form.notes,
      });
      await loadClaims(selectedZone);
      setForm({ ...form, lengthCm: "", notes: "" });
    } catch (err) {
      console.error("Error logging catch", err);
      alert("Error logging catch – see console.");
    }
  };

  return (
    <div
      style={{
        fontFamily: "system-ui, sans-serif",
        background: "#111827",
        minHeight: "100vh",
        color: "#e5e7eb",
      }}
    >
      {/* 2-column layout: LEFT controls, RIGHT map */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "360px 1fr",
          height: "100vh", // 👈 guarantees the map column has height
          width: "100%",
        }}
      >
        {/* LEFT PANE — controls */}
        <aside
          style={{
            padding: "1rem",
            overflowY: "auto",
            borderRight: "1px solid rgba(255,255,255,0.06)",
            background: "#0b1220",
          }}
        >
          <h1 style={{ fontSize: "1.6rem", marginBottom: "0.25rem" }}>FishClaim UI</h1>
          <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
            Connected to: <code>{API_BASE}</code>
          </p>

          {/* 🔐 Auth */}
          <section
            style={{
              marginTop: "1rem",
              padding: "0.75rem 1rem",
              background: "#020617",
              borderRadius: "0.5rem",
            }}
          >
            <h2>Login</h2>
            {!token ? (
              <form onSubmit={handleLogin}>
                <div style={{ marginBottom: "0.5rem" }}>
                  <label>
                    Username:
                    <input
                      type="text"
                      value={loginForm.username}
                      onChange={(e) =>
                        setLoginForm({ ...loginForm, username: e.target.value })
                      }
                      style={{ marginLeft: "0.5rem" }}
                    />
                  </label>
                </div>
                <div style={{ marginBottom: "0.5rem" }}>
                  <label>
                    Password:
                    <input
                      type="password"
                      value={loginForm.password}
                      onChange={(e) =>
                        setLoginForm({ ...loginForm, password: e.target.value })
                      }
                      style={{ marginLeft: "0.5rem" }}
                    />
                  </label>
                </div>
                <button
                  type="submit"
                  style={{
                    padding: "0.3rem 0.8rem",
                    background: "#2563eb",
                    border: "none",
                    borderRadius: "0.375rem",
                    color: "white",
                    cursor: "pointer",
                  }}
                >
                  Log In
                </button>
              </form>
            ) : (
              <div>
                <p style={{ marginBottom: "0.5rem" }}>
                  Logged in. Token is set on Axios.
                </p>
                <button
                  onClick={handleLogout}
                  style={{
                    padding: "0.3rem 0.8rem",
                    background: "#b91c1c",
                    border: "none",
                    borderRadius: "0.375rem",
                    color: "white",
                    cursor: "pointer",
                  }}
                >
                  Log Out
                </button>
              </div>
            )}
          </section>

          {/* Waters */}
          <section style={{ marginTop: "1.5rem" }}>
            <h2>Waters</h2>
            {watersLoading && <p>Loading waters...</p>}
            {watersError && (
              <p style={{ color: "#f87171" }}>{watersError}</p>
            )}
            {waters.map((w) => (
              <button
                key={w.id}
                onClick={() => loadZones(w)}
                style={{
                  display: "block",
                  marginBottom: "0.3rem",
                  background: "#0ea5e9",
                  color: "white",
                  border: "none",
                  borderRadius: "0.5rem",
                  padding: "0.35rem 0.7rem",
                  cursor: "pointer",
                }}
              >
                {w.name} ({w.region})
              </button>
            ))}
          </section>

          {/* Zones */}
          {selectedWater && (
            <section style={{ marginTop: "1.5rem" }}>
              <h2>Zones in {selectedWater.name}</h2>
              {zonesLoading && <p>Loading zones...</p>}
              {zonesError && <p style={{ color: "#f87171" }}>{zonesError}</p>}
              {zones.map((z) => (
                <button
                  key={z.id}
                  onClick={() => loadClaims(z)}
                  style={{
                    display: "block",
                    marginBottom: "0.3rem",
                    background: "#10b981",
                    color: "white",
                    border: "none",
                    borderRadius: "0.5rem",
                    padding: "0.35rem 0.7rem",
                    cursor: "pointer",
                  }}
                >
                  {z.name}
                </button>
              ))}
            </section>
          )}

          {/* Claims */}
          {selectedZone && (
            <section style={{ marginTop: "1.5rem" }}>
              <h2>Claims in {selectedZone.name}</h2>
              {claimsLoading && <p>Loading claims...</p>}
              {claimsError && <p style={{ color: "#f87171" }}>{claimsError}</p>}
              {!claimsLoading && claims.length === 0 ? (
                <p>No active claims yet.</p>
              ) : (
                <ul>
                  {claims.map((c) => (
                    <li key={c.id}>
                      Species #{c.species_id} — {c.length_cm} cm (user #{c.user_id})
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}

          {/* Log Catch Form */}
          {selectedZone && (
            <section style={{ marginTop: "1.5rem" }}>
              <h2>Log Catch in {selectedZone.name}</h2>
              <form onSubmit={handleLogCatch}>
                <div style={{ marginBottom: "0.5rem" }}>
                  <label>
                    Species:
                    <select
                      value={form.speciesId}
                      onChange={(e) =>
                        setForm({ ...form, speciesId: e.target.value })
                      }
                      style={{ marginLeft: "0.5rem" }}
                    >
                      <option value="1">Brown Trout</option>
                      <option value="2">Rainbow Trout</option>
                    </select>
                  </label>
                </div>
                <div style={{ marginBottom: "0.5rem" }}>
                  <label>
                    Length (cm):
                    <input
                      type="number"
                      step="0.1"
                      value={form.lengthCm}
                      onChange={(e) =>
                        setForm({ ...form, lengthCm: e.target.value })
                      }
                      style={{ marginLeft: "0.5rem" }}
                      required
                    />
                  </label>
                </div>
                <div style={{ marginBottom: "0.5rem" }}>
                  <label>
                    Method:
                    <input
                      type="text"
                      value={form.method}
                      onChange={(e) =>
                        setForm({ ...form, method: e.target.value })
                      }
                      style={{ marginLeft: "0.5rem" }}
                    />
                  </label>
                </div>
                <div style={{ marginBottom: "0.5rem" }}>
                  <label>
                    Notes:
                    <input
                      type="text"
                      value={form.notes}
                      onChange={(e) =>
                        setForm({ ...form, notes: e.target.value })
                      }
                      style={{ marginLeft: "0.5rem", width: "250px" }}
                    />
                  </label>
                </div>
                <button
                  type="submit"
                  style={{
                    padding: "0.35rem 0.8rem",
                    background: "#2563eb",
                    border: "none",
                    borderRadius: "0.375rem",
                    color: "white",
                    cursor: "pointer",
                  }}
                >
                  Submit Catch
                </button>
              </form>
            </section>
          )}
        </aside>

      {/* RIGHT PANE — live map */}
      <main
        style={{
          position: "relative",
          height: "100%",         // fill parent
          minHeight: 0,
          overflow: "hidden",     // prevent scrollbars on map
        }}
      >
        {!token ? (
          <div
            style={{
              height: "100%",
              display: "grid",
              placeItems: "center",
              color: "#94a3b8",
            }}
          >
            Log in to view the map.
          </div>
        ) : (
          <div
            style={{
              height: "100%",
              width: "100%",
              background: "#0b1220",
            }}
          >
            <MapView token={token} onAuthError={handleLogout} /> {/* ✅ active again */}
          </div>
        )}
      </main>

      </div>
    </div>
  );
}

export default App;
