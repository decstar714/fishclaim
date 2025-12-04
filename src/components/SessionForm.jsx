import { useState } from "react";
import axios from "axios";

export default function SessionForm({ waters, zones, species, onCreated, apiBase, token }) {
  const [form, setForm] = useState({
    water_id: "",
    zone_id: "",
    species_id: "",
    best_length_cm: "",
    duration_minutes: "",
    method: "",
    notes: "",
    conditions: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        water_id: Number(form.water_id),
        zone_id: Number(form.zone_id),
        species_id: form.species_id ? Number(form.species_id) : null,
        best_length_cm: form.best_length_cm ? Number(form.best_length_cm) : null,
        duration_minutes: form.duration_minutes ? Number(form.duration_minutes) : null,
        method: form.method || null,
        notes: form.notes || null,
        conditions: form.conditions || null,
      };
      const res = await axios.post(`${apiBase}/sessions`, payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
      onCreated?.(res.data);
      setForm({
        water_id: "",
        zone_id: "",
        species_id: "",
        best_length_cm: "",
        duration_minutes: "",
        method: "",
        notes: "",
        conditions: "",
      });
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.detail || "Failed to save session");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.5rem" }}>
      <div>
        <label>
          Water:
          <select value={form.water_id} onChange={handleChange("water_id")} required>
            <option value="">Select water</option>
            {waters.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div>
        <label>
          Zone:
          <select value={form.zone_id} onChange={handleChange("zone_id")} required>
            <option value="">Select zone</option>
            {zones
              .filter((z) => !form.water_id || z.water_id === Number(form.water_id))
              .map((z) => (
                <option key={z.id} value={z.id}>
                  {z.name}
                </option>
              ))}
          </select>
        </label>
      </div>
      <div>
        <label>
          Species (optional):
          <select value={form.species_id} onChange={handleChange("species_id")}>
            <option value="">Select species</option>
            {species.map((s) => (
              <option key={s.id} value={s.id}>
                {s.common_name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div>
        <label>
          Best length (cm):
          <input
            type="number"
            value={form.best_length_cm}
            onChange={handleChange("best_length_cm")}
            min="0"
            step="0.1"
          />
        </label>
      </div>
      <div>
        <label>
          Duration (minutes):
          <input
            type="number"
            value={form.duration_minutes}
            onChange={handleChange("duration_minutes")}
            min="0"
          />
        </label>
      </div>
      <div>
        <label>
          Method:
          <input type="text" value={form.method} onChange={handleChange("method")} />
        </label>
      </div>
      <div>
        <label>
          Conditions:
          <input type="text" value={form.conditions} onChange={handleChange("conditions")} />
        </label>
      </div>
      <div>
        <label>
          Notes:
          <textarea value={form.notes} onChange={handleChange("notes")} />
        </label>
      </div>
      {error && <p style={{ color: "#f87171" }}>{error}</p>}
      <button
        type="submit"
        disabled={saving}
        style={{
          padding: "0.35rem 0.8rem",
          background: "#0ea5e9",
          color: "white",
          border: "none",
          borderRadius: "0.4rem",
          cursor: "pointer",
        }}
      >
        {saving ? "Saving..." : "Log Session"}
      </button>
    </form>
  );
}
