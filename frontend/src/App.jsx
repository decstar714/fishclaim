// src/App.jsx
import { useEffect, useState } from "react";
import axios from "axios";
import MapView from "./features/map/MapView"; // 👈 direct default import
import SessionForm from "./components/SessionForm";

const API_BASE = import.meta.env.VITE_API_BASE_URL; // keep your current var

function App() {
  const [waters, setWaters] = useState([]);
  const [zones, setZones] = useState([]);
  const [claims, setClaims] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [species, setSpecies] = useState([]);
  const [selectedWater, setSelectedWater] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);

  // auth state
  const [token, setToken] = useState(localStorage.getItem("auth_token") || "");
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [isRegistering, setIsRegistering] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    username: "",
    email: "",
    password: "",
    display_name: "",
  });
  const [sessionZones, setSessionZones] = useState([]);

  // catch form state
  const [form, setForm] = useState({
    speciesId: "1",
    lengthCm: "",
    method: "fly",
    notes: "",
  });

  // set axios auth header if token exists on first load/refresh
  useEffect(() => {
    if (token) axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  }, [token]);

  const loadWaters = async () => {
    try {
      const res = await axios.get(`${API_BASE}/waters/`);
      setWaters(res.data);
    } catch (err) {
      console.error("Error loading waters", err);
    }
  };

  const loadSpecies = async () => {
    try {
      const res = await axios.get(`${API_BASE}/species/`);
      const items = res.data || [];
      setSpecies(items);
      if (items.length) {
        setForm((prev) => ({
          ...prev,
          speciesId: prev.speciesId || String(items[0].id),
        }));
      }
    } catch (err) {
      console.error("Error loading species", err);
      setSpecies([]);
    }
  };

  // Load data on first render
  useEffect(() => {
    loadWaters();
    loadSpecies();
  }, []);

  const loadZones = async (water) => {
    setSelectedWater(water);
    setSelectedZone(null);
    setClaims([]);
    try {
      const res = await axios.get(`${API_BASE}/waters/${water.id}/zones`);
      setZones(res.data);
      setSessionZones(res.data);
    } catch (err) {
      console.error("Error loading zones", err);
    }
  };

  const loadClaims = async (zone) => {
    setSelectedZone(zone);
    try {
      const res = await axios.get(`${API_BASE}/claims/zone/${zone.id}`);
      setClaims(res.data);
    } catch (err) {
      console.error("Error loading claims", err);
      setClaims([]);
    }
  };

  useEffect(() => {
    if (token) {
      loadSessions();
    }
  }, [token]);

  const loadSessions = async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE}/sessions`);
      setSessions(res.data);
    } catch {
      // non-blocking
    }
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
      localStorage.setItem("auth_token", t);
      axios.defaults.headers.common["Authorization"] = `Bearer ${t}`;
      alert("Logged in as " + loginForm.username);
    } catch (err) {
      console.error("Login failed", err);
      alert("Login failed – check username/password or backend logs.");
    }
  };

  // 📝 Register handler
  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/auth/register`, {
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password,
        display_name: registerForm.display_name || undefined,
      });
      alert("Registration successful! Please log in.");
      setIsRegistering(false);
      setLoginForm({
        username: registerForm.username,
        password: registerForm.password,
      });
    } catch (err) {
      console.error("Registration failed", err);
      alert("Registration failed – check console/backend logs.");
    }
  };

  const handleLogout = () => {
    setToken("");
    localStorage.removeItem("auth_token");
    delete axios.defaults.headers.common["Authorization"];
  };

  const onSessionCreated = () => {
    loadSessions();
    if (selectedZone) loadClaims(selectedZone);
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
              isRegistering ? (
                <form onSubmit={handleRegister}>
                  <div style={{ marginBottom: "0.5rem" }}>
                    <label>
                      Username:
                      <input
                        type="text"
                        value={registerForm.username}
                        onChange={(e) =>
                          setRegisterForm({ ...registerForm, username: e.target.value })
                        }
                        style={{ marginLeft: "0.5rem" }}
                        required
                      />
                    </label>
                  </div>
                  <div style={{ marginBottom: "0.5rem" }}>
                    <label>
                      Email:
                      <input
                        type="email"
                        value={registerForm.email}
                        onChange={(e) =>
                          setRegisterForm({ ...registerForm, email: e.target.value })
                        }
                        style={{ marginLeft: "0.5rem" }}
                        required
                      />
                    </label>
                  </div>
                  <div style={{ marginBottom: "0.5rem" }}>
                    <label>
                      Password:
                      <input
                        type="password"
                        value={registerForm.password}
                        onChange={(e) =>
                          setRegisterForm({ ...registerForm, password: e.target.value })
                        }
                        style={{ marginLeft: "0.5rem" }}
                        required
                      />
                    </label>
                  </div>
                  <div style={{ marginBottom: "0.5rem" }}>
                    <label>
                      Display Name:
                      <input
                        type="text"
                        value={registerForm.display_name}
                        onChange={(e) =>
                          setRegisterForm({
                            ...registerForm,
                            display_name: e.target.value,
                          })
                        }
                        style={{ marginLeft: "0.5rem" }}
                      />
                    </label>
                  </div>
                  <button
                    type="submit"
                    style={{
                      padding: "0.3rem 0.8rem",
                      background: "#10b981",
                      border: "none",
                      borderRadius: "0.375rem",
                      color: "white",
                      cursor: "pointer",
                      marginRight: "0.5rem",
                    }}
                  >
                    Sign Up
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsRegistering(false)}
                    style={{
                      padding: "0.3rem 0.8rem",
                      background: "transparent",
                      border: "1px solid #4b5563",
                      borderRadius: "0.375rem",
                      color: "#9ca3af",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                </form>
              ) : (
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
                      marginRight: "0.5rem",
                    }}
                  >
                    Log In
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsRegistering(true)}
                    style={{
                      padding: "0.3rem 0.8rem",
                      background: "transparent",
                      border: "1px solid #4b5563",
                      borderRadius: "0.375rem",
                      color: "#9ca3af",
                      cursor: "pointer",
                    }}
                  >
                    Sign Up
                  </button>
                </form>
              )
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

          {/* Log Session */}
          {token && (
            <section style={{ marginTop: "1.5rem" }}>
              <h2>Log Session (zone-level)</h2>
              <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
                Refresh your claim by recording time on water. No exact spots stored.
              </p>
              <SessionForm
                waters={waters}
                zones={zones}
                species={species}
                apiBase={API_BASE}
                token={token}
                onCreated={onSessionCreated}
              />
            </section>
          )}

          {/* Claims */}
          {selectedZone && (
            <section style={{ marginTop: "1.5rem" }}>
              <h2>Claims in {selectedZone.name}</h2>
              {claims.length === 0 ? (
                <p>No active claims yet.</p>
              ) : (
                <ul>
                  {claims.map((c) => (
                    <li key={c.id}>
                      Species #{c.species_id} — {c.length_cm} cm (user #{c.user_id})
                      {c.expires_at && (
                        <div style={{ fontSize: "0.85rem", opacity: 0.75 }}>
                          Expires: {new Date(c.expires_at).toLocaleString()}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
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
              <MapView token={token} /> {/* ✅ active again */}
            </div>
          )}
        </main>

      </div>
    </div>
  );
}

export default App;
