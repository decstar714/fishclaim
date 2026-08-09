import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function ClaimLeaderboard() {
  const [leaders, setLeaders] = useState([]);
  const [err, setErr] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API_BASE}/stats/claims`);
        setLeaders(res.data?.leaders || []);
      } catch (e) {
        setErr(e?.message || "Failed to load leaderboard");
      }
    };
    load();
  }, []);

  return (
    <div style={{ background: "#111827", color: "#e5e7eb", border: "1px solid #1f2937", borderRadius: 8, padding: "0.75rem" }}>
      <div style={{ fontWeight: 600, marginBottom: "0.35rem" }}>Claim Leaderboard</div>
      {err && <div style={{ color: "#f87171", fontSize: "0.85rem" }}>{err}</div>}
      {leaders.length === 0 && !err && <div style={{ fontSize: "0.85rem", opacity: 0.8 }}>No active claims yet.</div>}
      {leaders.map((l, idx) => (
        <div key={`${l.user_id}-${idx}`} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.9rem", padding: "2px 0" }}>
          <span>#{idx + 1} {l.user_id}</span>
          <span>{l.active_claims} active</span>
        </div>
      ))}
    </div>
  );
}
