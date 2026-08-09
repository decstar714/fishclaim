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

export default function MapView({ token }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const fitted = useRef(false);
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
        // A claim has no shape of its own -- it borrows the reach it was won on,
        // so it is drawn as a line over the river rather than as a fill. A fill
        // renders nothing at all for a LineString, which is why the map used to
        // look empty even with data in it.
        map.addLayer({
          id: "claims-glow",
          type: "line",
          source: "claims",
          paint: {
            "line-color": "#f59e0b",
            "line-opacity": 0.35,
            "line-width": ["interpolate", ["linear"], ["zoom"], 8, 8, 12, 16],
            "line-blur": 3,
          },
        });
        map.addLayer({
          id: "claims-line",
          type: "line",
          source: "claims",
          paint: {
            "line-color": "#f59e0b",
            "line-width": ["interpolate", ["linear"], ["zoom"], 8, 2.5, 12, 5],
          },
        });

        map.on("click", "claims-line", (e) => {
          const p = e.features?.[0]?.properties || {};
          new maplibregl.Popup({ closeButton: false })
            .setLngLat(e.lngLat)
            .setHTML(
              `<div style="font:13px system-ui">
                 <strong>${p.zone_name ?? "Zone"}</strong><br/>
                 ${p.species ?? "?"} — ${p.length_cm} cm<br/>
                 <span style="opacity:.7">angler #${p.user_id}</span>
               </div>`
            )
            .addTo(map);
        });
        map.on("mouseenter", "claims-line", () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "claims-line", () => { map.getCanvas().style.cursor = ""; });
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

          // Frame the water once, the first time any arrives. Only once --
          // fitting on every load would fight the user every time they panned,
          // and moveend is what triggers this in the first place.
          if (!fitted.current && riversFc.features.length) {
            const b = new maplibregl.LngLatBounds();
            for (const f of riversFc.features) {
              const parts =
                f.geometry.type === "MultiLineString"
                  ? f.geometry.coordinates.flat()
                  : f.geometry.coordinates;
              for (const c of parts) b.extend([c[0], c[1]]);
            }
            fitted.current = true;
            map.fitBounds(b, { padding: 60, duration: 800, maxZoom: 13 });
          }
        } catch (e) {
          console.warn("[API] fetch fail", e);
          setErr(String(e?.message || e));
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
