import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { fetchRiversByBbox, fetchClaimsByBbox } from "./api";

const STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const CENTER = [-74.742, 40.612];
const ZOOM = 10;

function bboxFromMap(map) {
  const b = map.getBounds();
  return { minX: b.getWest(), minY: b.getSouth(), maxX: b.getEast(), maxY: b.getNorth() };
}
function debounce(fn, ms = 250) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

export default function MapView({ token, onAuthError }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);
  const [counts, setCounts] = useState({ rivers: 0, claims: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    el.style.position = "absolute";
    el.style.inset = "0";
    el.style.height = "100%";
    el.style.width = "100%";

    const map = new maplibregl.Map({
      container: el,
      style: STYLE,
      center: CENTER,
      zoom: ZOOM,
      attributionControl: false,
    });
    mapRef.current = map;
    window.fcMap = map; // debug

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    const ro = new ResizeObserver(() => map.resize());
    ro.observe(el);
    map.__ro = ro;

    map.on("error", (e) => {
      console.error("[Map] error", e?.error || e);
      setErr(String(e?.error?.message || e?.message || e));
    });

    // create sources/layers once
    map.on("load", () => {
      if (!map.getSource("rivers")) {
        map.addSource("rivers", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        map.addLayer({
          id: "rivers-line",
          type: "line",
          source: "rivers",
          paint: {
            "line-color": "#2b7abf",
            "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.8, 8, 2.2, 12, 3.5],
          },
        });
      }
      if (!map.getSource("claims")) {
        map.addSource("claims", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        map.addLayer({
          id: "claims-fill",
          type: "fill",
          source: "claims",
          paint: { "fill-color": ["coalesce", ["get", "color"], "#f59e0b"], "fill-opacity": 0.35 },
        });
        map.addLayer({
          id: "claims-outline",
          type: "line",
          source: "claims",
          paint: { "line-color": "#2b2b2b", "line-width": 1 },
        });
      }

      const refetch = debounce(async () => {
        if (!token) return; // gate until logged-in
        const bbox = bboxFromMap(map);
        try {
          setLoading(true);
          setErr(null);
          const [r, c] = await Promise.all([
            fetchRiversByBbox(token, bbox), // → { features: [...] }
            fetchClaimsByBbox(token, bbox), // → { claims: [...] }
          ]);
          const riversFc = { type: "FeatureCollection", features: r?.features || [] };
          const claimsFc = {
            type: "FeatureCollection",
            features: (c?.claims || []).map((x) => ({ type: "Feature", properties: { ...x }, geometry: x.geometry })),
          };
          map.getSource("rivers").setData(riversFc);
          map.getSource("claims").setData(claimsFc);
          setCounts({ rivers: riversFc.features.length, claims: claimsFc.features.length });
        } catch (e) {
          console.warn("[API] fetch fail", e);
          const status = e?.status;
          if (status === 401 || status === 403) {
            const emptyFc = { type: "FeatureCollection", features: [] };
            map.getSource("rivers")?.setData(emptyFc);
            map.getSource("claims")?.setData(emptyFc);
            setCounts({ rivers: 0, claims: 0 });
            setErr("Session expired—please log in again");
            if (typeof onAuthError === "function") onAuthError();
            if (typeof window !== "undefined" && typeof window.fcHandleAuthError === "function") {
              window.fcHandleAuthError();
            }
          } else {
            setErr(String(e?.message || e));
          }
        } finally {
          setLoading(false);
        }
      }, 250);

      refetch();
      map.on("moveend", refetch);
    });

    // cleanup
    return () => {
      try {
        map.__ro?.disconnect?.();
      } catch (e) {
        console.warn("Map observer cleanup failed", e);
      }
      map.remove();
      mapRef.current = null;
    };
  }, [token]);

  return (
    <div style={{ position: "relative", height: "100%", width: "100%" }}>
      <div ref={containerRef} />
      {/* HUD */}
      <div style={{ position: "absolute", left: 8, top: 8, display: "flex", gap: 8 }}>
        <div style={{ background: "rgba(255,255,255,.9)", borderRadius: 12, padding: "6px 10px" }}>
          <strong style={{ fontSize: 12 }}>FishClaim</strong>
          <div style={{ fontSize: 10, opacity: .8 }}>Map MVP</div>
          <div style={{ fontSize: 10, opacity: .8, marginTop: 4 }}>
            {loading ? "Loading…" : `Rivers: ${counts.rivers} • Claims: ${counts.claims}`}
          </div>
        </div>
        {err && (
          <div style={{ background: "#dc2626", color: "#fff", borderRadius: 12, padding: "6px 10px", fontSize: 12, maxWidth: 360 }}>
            {err}
          </div>
        )}
      </div>
    </div>
  );
}
