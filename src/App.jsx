// src/App.jsx
import { useEffect, useState } from "react";
import axios from "axios";
import {
  clearSession,
  loadStoredSession,
  parseTokenResponse,
  refreshSession,
  registerAuthInterceptor,
  setSessionTokens,
} from "./auth/token";
import MapView from "./features/map/MapView";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

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
  const [authMessage, setAuthMessage] = useState("");
  const [currentUser, setCurrentUser] = useState(null);

  const [session, setSession] = useState(() => loadStoredSession());
  const accessToken = session?.accessToken || "";
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });

  const [form, setForm] = useState({
    speciesId: "1",
    lengthCm: "",
    method: "fly",
    notes: "",
  });

  useEffect(() => {
    const ejectAuthInterceptor = registerAuthInterceptor({
      apiBase: API_BASE,
      onUnauthorized: () => {
        setSession({ accessToken: "", refreshToken: "" });
        setCurrentUser(null);
        setAuthMessage("Session expired. Please log in again.");
      },
      onTokenRefreshed: (tokens) => {
        setSession(tokens);
        setAuthMessage("Session refreshed.");
        fetchMe();
      },
    });

    return ejectAuthInterceptor;
  }, []);

  const fetchMe = async () => {
    if (!accessToken) return;
    try {
      const res = await axios.get(`${API_BASE}/auth/me`);
      setCurrentUser(res.data);
      setAuthMessage("");
    } catch (err) {
      console.warn("Fetch me failed", err);
      handleLogout();
      setAuthMessage("Session expired. Please log in again.");
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchMe();
    } else {
      setCurrentUser(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  useEffect(() => {
    setWatersLoading(true);
    setWatersError("");
    axios
      .get(`${API_BASE}/waters/`)
      .then((res) => setWaters(res.data))
      .catch(() => setWatersError("Failed to load waters."))
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

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append("username", loginForm.username);
      params.append("password", loginForm.password);

      const res = await axios.post(`${API_BASE}/auth/login`, params, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const tokens = parseTokenResponse(res.data);
      setSessionTokens(tokens);
      setSession(tokens);
      setAuthMessage("Logged in.");
      await fetchMe();
    } catch (err) {
      console.error("Login failed", err);
      alert("Login failed – check username/password or backend logs.");
    }
  };

  const handleLogout = () => {
    clearSession();
    setSession({ accessToken: "", refreshToken: "" });
    setCurrentUser(null);
  };

  const handleAuthRecovery = async () => {
    try {
      const tokens = await refreshSession(API_BASE);
      setSession(tokens);
      setAuthMessage("Session refreshed.");
      await fetchMe();
      return true;
    } catch (err) {
      console.warn("Session refresh failed", err);
      handleLogout();
      setAuthMessage("Session expired. Please log in again.");
      return false;
    }
  };

  const handleLogCatch = async (e) => {
    e.preventDefault();
    if (!accessToken) {
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

  const updateClaimStatus = async (claimId, status) => {
    if (!accessToken) return;
    let review_notes = undefined;
    if (status === "rejected") {
      const note = window.prompt("Enter rejection reason:");
      if (note !== null) {
        review_notes = note;
      }
    }
    try {
      await axios.post(`${API_BASE}/claims/${claimId}/status`, {
        status,
        review_notes,
      });
      if (selectedZone) {
        await loadClaims(selectedZone);
      }
      setAuthMessage("Claim status updated.");
    } catch (err) {
      console.error("Failed to update status", err);
      alert("Failed to update status. Check console/back-end.");
    }
  };

  const canReview = currentUser?.role === "admin" || currentUser?.role === "reviewer";

  return (
    <div
      style={{
        fontFamily: "system-ui, sans-serif",
        background: "#111827",
        minHeight: "100vh",
        color: "#e5e7eb",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "360px 1fr",
          height: "100vh",
          width: "100%",
        }}
      >
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
          {currentUser && (
            <p style={{ fontSize: "0.9rem", marginTop: "0.25rem" }}>
              User: <strong>{currentUser.display_name || currentUser.username}</strong> ({currentUser.role})
            </p>
          )}
          {authMessage && (
            <div style={{ marginTop: "0.5rem", color: "#93c5fd", fontSize: "0.95rem" }}>
              {authMessage}
            </div>
          )}

          <section
            style={{
              marginTop: "1rem",
              padding: "0.75rem 1rem",
              background: "#020617",
              borderRadius: "0.5rem",
            }}
          >
            <h2>Login</h2>
            {!accessToken ? (
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
                    <li key={c.id} style={{ marginBottom: "0.4rem" }}>
                      <div>
                        Species #{c.species_id} — {c.length_cm} cm (user #{c.user_id}) —{" "}
                        <strong>{c.status}</strong>
                      </div>
                      {c.review_notes && (
                        <div style={{ fontSize: "0.9rem", color: "#93c5fd" }}>
                          Notes: {c.review_notes}
                        </div>
                      )}
                      {canReview && (
                        <div style={{ marginTop: "0.3rem", display: "flex", gap: "0.4rem" }}>
                          <button
                            onClick={() => updateClaimStatus(c.id, "under_review")}
                            style={{ padding: "0.25rem 0.5rem" }}
                          >
                            Under Review
                          </button>
                          <button
                            onClick={() => updateClaimStatus(c.id, "approved")}
                            style={{ padding: "0.25rem 0.5rem" }}
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => updateClaimStatus(c.id, "rejected")}
                            style={{ padding: "0.25rem 0.5rem", background: "#f87171", border: "none", borderRadius: "0.25rem" }}
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}

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

        <main
          style={{
            position: "relative",
            height: "100%",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          {!accessToken ? (
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
              <MapView token={accessToken} onAuthError={handleAuthRecovery} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
