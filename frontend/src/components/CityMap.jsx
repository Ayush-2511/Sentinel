import React, { useEffect, useRef } from "react"
import { MapContainer, TileLayer, Polygon, Tooltip, useMap } from "react-leaflet"
import "leaflet/dist/leaflet.css"

// Lucknow center coordinates
const CENTER = [26.8467, 80.9500]
const ZOOM = 14

const HAZARD_ICONS = {
  structural_collapse: "🏚️",
  fire: "🔥",
  flooding: "🌊",
  gas_leak: "⚠️",
}

const INFRA_LABELS = {
  intact: { text: "INTACT", color: "#2ecc71" },
  damaged: { text: "DAMAGED", color: "#f39c12" },
  destroyed: { text: "DESTROYED", color: "#e74c3c" },
}

// Fire-aware fill color
function getFillColor(sector) {
  const fire = sector.fire_intensity || 0
  const infra = sector.infrastructure

  if (infra === "destroyed") return "#3D1A0A"
  if (fire > 0.7) return "#B91C1C"  // Intense fire
  if (fire > 0.4) return "#DC2626"  // Medium fire
  if (fire > 0.1) return "#9A3412"  // Smoldering
  if (sector.severity_score >= 0.7) return "#8B0000"
  if (sector.severity_score >= 0.4) return "#B8860B"
  if (sector.severity_score > 0.05) return "#006400"
  return "#0A2530"
}

function getFillOpacity(sector) {
  const fire = sector.fire_intensity || 0
  if (fire > 0) return Math.min(0.75, 0.35 + fire * 0.45)
  return Math.min(0.65, 0.2 + sector.severity_score * 0.5)
}

function getBorderColor(sector, isWinner) {
  if (isWinner) return "#00d4b8"
  const fire = sector.fire_intensity || 0
  if (fire > 0.5) return "#EF4444"
  if (fire > 0) return "#F97316"
  return "#1a3045"
}

// Component to fit bounds when sectors change
function FitBounds({ sectors }) {
  const map = useMap()
  const fitted = useRef(false)

  useEffect(() => {
    if (sectors && sectors.length > 0 && !fitted.current) {
      const allCoords = sectors.flatMap(s => s.polygon || [])
      if (allCoords.length > 0) {
        map.fitBounds(allCoords, { padding: [30, 30] })
        fitted.current = true
      }
    }
  }, [sectors, map])

  return null
}

export default function CityMap({ gridState, lastWinnerSector }) {
  if (!gridState || !gridState.sectors) {
    return (
      <div className="flex items-center justify-center h-full text-muted text-xs font-mono tracking-widest">
        SELECT A SCENARIO TO BEGIN
      </div>
    )
  }

  const sectors = gridState.sectors

  return (
    <div className="h-full w-full relative" style={{ background: "#0a0e14" }}>
      <MapContainer
        center={CENTER}
        zoom={ZOOM}
        className="h-full w-full"
        zoomControl={false}
        attributionControl={false}
        style={{ background: "#0a0e14" }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />

        <FitBounds sectors={sectors} />

        {sectors.map(sector => {
          const polygon = sector.polygon
          if (!polygon || polygon.length < 3) return null

          const isWinner = lastWinnerSector === sector.id
          const fillColor = getFillColor(sector)
          const borderColor = getBorderColor(sector, isWinner)
          const infraInfo = INFRA_LABELS[sector.infrastructure] || INFRA_LABELS.intact
          const civ = sector.civilians
          const dep = sector.resources_deployed
          const fire = sector.fire_intensity || 0
          const spreadRate = sector.fire_spread_rate || 0

          return (
            <Polygon
              key={sector.id}
              positions={polygon}
              pathOptions={{
                color: borderColor,
                weight: isWinner ? 3 : fire > 0 ? 2 : 1.5,
                fillColor: fillColor,
                fillOpacity: getFillOpacity(sector),
                dashArray: isWinner ? "" : fire > 0 ? "" : "4 2",
              }}
            >
              <Tooltip
                direction="top"
                sticky
                className="sentinel-tooltip"
              >
                <div style={{
                  background: "#0d1117",
                  border: `1px solid ${borderColor}`,
                  borderRadius: "4px",
                  padding: "10px 14px",
                  color: "#e0e0e0",
                  fontFamily: "'Consolas', 'Courier New', monospace",
                  fontSize: "11px",
                  minWidth: "220px",
                  lineHeight: "1.6",
                }}>
                  {/* Header */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <span style={{ color: "#00d4b8", fontWeight: "bold", fontSize: "13px", letterSpacing: "2px" }}>
                      {sector.id}
                    </span>
                    <span style={{ color: infraInfo.color, fontSize: "9px", letterSpacing: "1px", border: `1px solid ${infraInfo.color}40`, padding: "1px 6px", borderRadius: "2px" }}>
                      {infraInfo.text}
                    </span>
                  </div>
                  <div style={{ color: "#fff", fontWeight: "600", fontSize: "12px", marginBottom: "6px" }}>
                    {sector.name} <span style={{ color: "#666", fontWeight: "400" }}>({sector.type})</span>
                  </div>

                  {/* Fire intensity bar */}
                  {fire > 0 && (
                    <div style={{ marginBottom: "6px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                        <span style={{ color: "#EF4444", fontWeight: "bold", fontSize: "10px" }}>🔥 FIRE: {(fire * 100).toFixed(0)}%</span>
                        <span style={{ color: "#666", fontSize: "9px" }}>SPREAD: {(spreadRate * 100).toFixed(0)}%/tick</span>
                      </div>
                      <div style={{ height: "4px", background: "#1a1a2e", borderRadius: "2px", overflow: "hidden" }}>
                        <div style={{
                          height: "100%",
                          width: `${fire * 100}%`,
                          background: fire > 0.6 ? "#EF4444" : fire > 0.3 ? "#F97316" : "#EAB308",
                          borderRadius: "2px",
                          transition: "width 0.5s",
                        }}></div>
                      </div>
                    </div>
                  )}
                  {fire === 0 && spreadRate > 0 && (
                    <div style={{ color: "#F97316", fontSize: "10px", marginBottom: "6px" }}>
                      ⚠ FIRE THREAT: {(spreadRate * 100).toFixed(0)}% chance from neighbors
                    </div>
                  )}

                  {/* Civilians */}
                  <div style={{ display: "flex", gap: "10px", marginBottom: "4px" }}>
                    {civ.critical > 0 && <span style={{ color: "#e74c3c", fontWeight: "bold" }}>{civ.critical} CRIT</span>}
                    {civ.stable > 0 && <span style={{ color: "#f39c12" }}>{civ.stable} STBL</span>}
                    {civ.rescued > 0 && <span style={{ color: "#2ecc71" }}>{civ.rescued} RESC</span>}
                  </div>

                  {/* Hazards */}
                  {sector.hazards.length > 0 && (
                    <div style={{ marginBottom: "4px" }}>
                      {sector.hazards.map(h => (
                        <span key={h} style={{ marginRight: "6px" }} title={h.replace(/_/g, " ")}>
                          {HAZARD_ICONS[h] || "⚠️"} {h.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Deployed Resources */}
                  {(dep.medical_teams > 0 || dep.rescue_units > 0 || dep.supply_caches > 0) && (
                    <div style={{ display: "flex", gap: "6px", marginTop: "4px" }}>
                      {dep.medical_teams > 0 && <span style={{ color: "#00d4b8", border: "1px solid #00d4b840", padding: "0 5px", borderRadius: "2px", fontSize: "10px" }}>+{dep.medical_teams} MED</span>}
                      {dep.rescue_units > 0 && <span style={{ color: "#f39c12", border: "1px solid #f39c1240", padding: "0 5px", borderRadius: "2px", fontSize: "10px" }}>{dep.rescue_units} RESC</span>}
                      {dep.supply_caches > 0 && <span style={{ color: "#3498db", border: "1px solid #3498db40", padding: "0 5px", borderRadius: "2px", fontSize: "10px" }}>{dep.supply_caches} SUP</span>}
                    </div>
                  )}

                  {/* Severity */}
                  <div style={{ marginTop: "6px", color: "#666", fontSize: "10px" }}>
                    SEVERITY: <span style={{ color: sector.severity_score >= 0.7 ? "#e74c3c" : sector.severity_score >= 0.4 ? "#f39c12" : "#2ecc71" }}>
                      {(sector.severity_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </Tooltip>
            </Polygon>
          )
        })}
      </MapContainer>

      <style>{`
        .sentinel-tooltip {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 0 !important;
        }
        .sentinel-tooltip::before {
          display: none !important;
        }
        .leaflet-container {
          background: #0a0e14 !important;
        }
      `}</style>
    </div>
  )
}
