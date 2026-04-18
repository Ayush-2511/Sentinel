import React, { useMemo, useState } from "react";
import clsx from "clsx";

export default function Grid({ gridState }) {
  const [hoveredCell, setHoveredCell] = useState(null); // { r, c, civ }

  const grid = useMemo(() => {
    if (gridState?.grid) return gridState.grid;
    const blank = [];
    for (let r = 0; r < 10; r++) blank.push(new Array(10).fill(0));
    return blank;
  }, [gridState?.grid]);

  // ── Cell rendering matching backend visualizer exactly ──────────────────────
  const getCellData = (r, c, val) => {
    const fireIntensity = gridState?.fire_map?.[r]?.[c] ?? 0;
    const integrity     = gridState?.building_integrity?.[r]?.[c] ?? 0;
    const isOnFire      = fireIntensity > 0.1;

    let bg        = "bg-[#1E1E23]";       // empty road — matches ROAD color
    let animation = "";
    let label     = "";
    let tooltip   = null;

    // ── Building (integrity > 0 means it's a standing/damaged building) ──────
    if (integrity > 0 && !isOnFire) {
      // Shade building based on integrity: high = solid gray, low = darker
      const shade = Math.round(80 + integrity * 0.55);   // 80–135 range
      const hex   = shade.toString(16).padStart(2, "0");
      bg = `bg-[#${hex}${hex}${Math.min(shade + 10, 255).toString(16).padStart(2, "0")}]`;
      tooltip = `Building integrity: ${Math.round(integrity)}%`;
    }

    // ── Fire overlay — beats everything except civilian/unit ─────────────────
    if (isOnFire) {
      bg        = fireIntensity > 3.0 ? "bg-[#6D1525]" : fireIntensity > 1.5 ? "bg-[#4D0F18]" : "bg-[#3D0A15]";
      bg       += " text-[#FF6B35]";
      animation = "animate-flicker";
      tooltip   = `Fire intensity: ${fireIntensity.toFixed(1)}`;
    }

    // ── Resource cache ────────────────────────────────────────────────────────
    if (val === 4 && !isOnFire) {
      bg    = "bg-[#0A1535] text-[#5090FF]";
      label = "R";
      tooltip = "Resource cache";
    }

    // ── Active units (medical/rescue on the map) ──────────────────────────────
    if (gridState?.active_units?.length) {
      const unit = gridState.active_units.find(u => u.pos?.[0] === r && u.pos?.[1] === c);
      if (unit) {
        bg        = unit.type === "medical" ? "bg-[#0A2530] text-teal" : "bg-[#1A1A0A] text-warning";
        animation = "animate-pulse-cell-slow";
        label     = unit.type === "medical" ? "M" : "U";
        tooltip   = `${unit.type} unit`;
        return { bg, animation, label, tooltip, civ: null };
      }
    }

    // ── Civilians ─────────────────────────────────────────────────────────────
    if (gridState?.civilians) {
      const saved = gridState.civilians.find(cv => cv.saved && cv.pos?.[0] === r && cv.pos?.[1] === c);
      if (saved) {
        bg      = "bg-[#0A2510]/70 text-success/60";
        label   = "✓";
        tooltip = `Civ #${saved.id} — SAVED`;
        return { bg, animation: "", label, tooltip, civ: saved };
      }

      const dead = gridState.civilians.find(cv => cv.health <= 0 && cv.pos?.[0] === r && cv.pos?.[1] === c);
      if (dead) {
        bg      = "bg-[#1A1A1A] text-muted/40";
        label   = "✕";
        tooltip = `Civ #${dead.id} — DEAD`;
        return { bg, animation: "", label, tooltip, civ: dead };
      }

      const civ = gridState.civilians.find(cv => !cv.saved && cv.health > 0 && cv.pos?.[0] === r && cv.pos?.[1] === c);
      if (civ) {
        if (civ.health > 60) {
          bg        = "bg-[#0A2510] text-success";
        } else if (civ.health >= 30) {
          bg        = "bg-[#251800] text-warning";
          animation = civ.health < 45 ? "animate-pulse-cell" : "";
        } else {
          bg        = "bg-[#2D0A15] text-danger";
          animation = "animate-pulse-cell";
        }
        label   = String(civ.id);
        tooltip = `Civ #${civ.id} | HP: ${Math.round(civ.health)} | ${civ.status?.toUpperCase()}${civ.hurt_rate > 0 ? ` | -${civ.hurt_rate}/tick` : ""}`;
        return { bg, animation, label, tooltip, civ };
      }
    }

    return { bg, animation, label, tooltip, civ: null };
  };

  const isRunning = gridState?.is_running;

  return (
    <>
      {/* Grid area */}
      <div className="flex-1 flex items-center justify-center py-6 px-4 relative tactical-bg overflow-hidden shadow-inner">

        {/* Grid wrapper with green corner brackets */}
        <div className="relative z-10">
          {/* Inner grid corner markers */}
          <div className="absolute -top-[3px] -left-[3px] w-3 h-3 pointer-events-none"
            style={{ borderTop: "1px solid rgba(46,180,90,0.35)", borderLeft: "1px solid rgba(46,180,90,0.35)", boxShadow: "0 0 4px rgba(46,180,90,0.12)" }} />
          <div className="absolute -top-[3px] -right-[3px] w-3 h-3 pointer-events-none"
            style={{ borderTop: "1px solid rgba(46,180,90,0.35)", borderRight: "1px solid rgba(46,180,90,0.35)", boxShadow: "0 0 4px rgba(46,180,90,0.12)" }} />
          <div className="absolute -bottom-[3px] -left-[3px] w-3 h-3 pointer-events-none"
            style={{ borderBottom: "1px solid rgba(46,180,90,0.35)", borderLeft: "1px solid rgba(46,180,90,0.35)", boxShadow: "0 0 4px rgba(46,180,90,0.12)" }} />
          <div className="absolute -bottom-[3px] -right-[3px] w-3 h-3 pointer-events-none"
            style={{ borderBottom: "1px solid rgba(46,180,90,0.35)", borderRight: "1px solid rgba(46,180,90,0.35)", boxShadow: "0 0 4px rgba(46,180,90,0.12)" }} />

          {/* Grid */}
          <div
            className="grid grid-cols-[repeat(10,1fr)] w-[min(calc(100vh-260px),calc(100vw-560px))] aspect-square max-w-[540px] max-h-[540px]"
            style={{ gap: "1px", background: "#1E3048", border: "1px solid #1E3048", padding: "1px" }}
          >
            {grid.map((rowArr, r) =>
              rowArr.map((val, c) => {
                const { bg, animation, label, tooltip, civ } = getCellData(r, c, val);
                const isHovered = hoveredCell?.r === r && hoveredCell?.c === c;

                return (
                  <div
                    key={`${r}-${c}`}
                    className={clsx(
                      "aspect-square flex items-center justify-center font-mono-custom text-[9px] font-bold relative cursor-pointer transition-all duration-300 ease-in-out animate-slide-in",
                      "hover:scale-[1.18] hover:z-20 hover:shadow-[0_0_14px_currentColor]",
                      bg, animation
                    )}
                    style={{ animationDelay: `${(r * 10 + c) * 3}ms` }}
                    onMouseEnter={() => setHoveredCell({ r, c, civ, tooltip })}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    {label}

                    {/* Hover tooltip */}
                    {isHovered && tooltip && (
                      <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 rounded-sm bg-navyCard border border-navyBorder shadow-lg pointer-events-none whitespace-nowrap"
                        style={{ minWidth: "120px" }}>
                        <div className="font-mono-custom text-[8px] text-white leading-relaxed text-center">
                          {tooltip.split(" | ").map((line, i) => (
                            <div key={i} className={i === 0 ? "text-teal font-bold" : "text-muted"}>{line}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-3 px-4 py-2 border-t border-navyBorder bg-navyCard flex-wrap">
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#1E1E23]" style={{border:"1px solid #1E3048"}}></div>EMPTY</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#787880]"></div>BUILDING</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#3D0A15]"></div>FIRE</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#0A2510]"></div>STABLE CIV</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#251800]"></div>INJ CIV</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#2D0A15]"></div>CRIT CIV</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#0A2530]"></div>MED UNIT</div>
      </div>
    </>
  );
}
