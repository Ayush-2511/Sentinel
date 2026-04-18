import React, { useMemo } from "react";
import clsx from "clsx";

export default function Grid({ gridState }) {
  // If no grid state exists yet, build a blank 10x10 array to render empty cells
  const grid = useMemo(() => {
    if (gridState?.grid) return gridState.grid;
    const blank = [];
    for (let r=0; r<10; r++) {
      blank.push(new Array(10).fill(0));
    }
    return blank;
  }, [gridState?.grid]);

  // Merge in civilians and active units dynamically onto grid for visual representation
  // Grid layout cell numbers from BUILD_GUIDE:
  // 0=empty, 1=collapsed, 2=fire, 3=civilian, 4=resource, 5=unit 
  // Custom cell types from sentinel_wireframe.html:
  // .c-empty     { background: #0A1A28; border: 1px solid #0D2035; }
  // .c-collapsed { background: #2D1A0A; border: 1px solid #4A2A0A; color: #7A4A20; }
  // .c-fire      { background: #3D0A15; border: 1px solid #7A1525; color: var(--red); animation: flicker... }
  // .c-critical  { background: #2D0A15; border: 1px solid var(--red); color: var(--red); animate pulse }
  // .c-stable    { background: #0A2510; border: 1px solid #0A4020; color: var(--green); }
  // .c-injured   { background: #251800; border: 1px solid #4A3000; color: var(--amber); }
  // .c-resource  { background: #0A1535; border: 1px solid #1535AA; color: #5090FF; }
  // .c-unit-med  { background: #0A2530; border: 1px solid var(--teal); color: var(--teal); animate pulse }
  // .c-unit-resc { background: #1A1A0A; border: 1px solid var(--amber); color: var(--amber); animate pulse }

  const getCellRendering = (r, c, val) => {
    // defaults
    let bg = "bg-[#0A1A28] border-[#0D2035]";
    let text = "";
    let animation = "";
    let label = "";

    if (val === 1) {
      bg = "bg-[#2D1A0A] border-[#4A2A0A] text-[#7A4A20]";
    } else if (val === 2) {
      bg = "bg-[#3D0A15] border-[#7A1525] text-danger";
      animation = "animate-flicker";
    } else if (val === 4) {
      bg = "bg-[#0A1535] border-[#1535AA] text-[#5090FF]";
    }

    // Lookup units
    if (gridState?.active_units) {
      const unit = gridState.active_units.find(u => u.pos && u.pos[0] === r && u.pos[1] === c);
      if (unit) {
        if (unit.type === 'medical') {
           bg = "bg-[#0A2530] border-teal text-teal";
           animation = "animate-pulse-cell-slow";
        } else if (unit.type === 'rescue') {
           bg = "bg-[#1A1A0A] border-warning text-warning";
           animation = "animate-pulse-cell-slow";
        }
        return { bg, animation, label: "U" };
      }
    }

    // Lookup civilians
    if (val === 3 && gridState?.civilians) {
      const civ = gridState.civilians.find(cv => cv.health > 0 && cv.pos && cv.pos[0] === r && cv.pos[1] === c);
      if (civ) {
        label = civ.id;
        if (civ.health > 60) {
          bg = "bg-[#0A2510] border-[#0A4020] text-success";
        } else if (civ.health >= 30) {
          bg = "bg-[#251800] border-[#4A3000] text-warning";
        } else {
          bg = "bg-[#2D0A15] border-danger text-danger";
          animation = "animate-pulse-cell";
        }
      }
    }

    return { bg, animation, label };
  };

  return (
    <>
      <div className="flex-1 flex items-center justify-center p-5 relative tactical-bg overflow-hidden shadow-inner">
        <div className="absolute w-4 h-4 border-tealDim opacity-80 top-2.5 left-2.5 border-t-2 border-l-2 shadow-[0_0_4px_var(--color-tealDim)]"></div>
        <div className="absolute w-4 h-4 border-tealDim opacity-80 top-2.5 right-2.5 border-t-2 border-r-2 shadow-[0_0_4px_var(--color-tealDim)]"></div>
        <div className="absolute w-4 h-4 border-tealDim opacity-80 bottom-2.5 left-2.5 border-b-2 border-l-2 shadow-[0_0_4px_var(--color-tealDim)]"></div>
        <div className="absolute w-4 h-4 border-tealDim opacity-80 bottom-2.5 right-2.5 border-b-2 border-r-2 shadow-[0_0_4px_var(--color-tealDim)]"></div>
        
        {/* Subtle grid background tracking lines overlay to make it feel tactical */}
        <div className="absolute inset-x-0 inset-y-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'linear-gradient(var(--color-teal) 1px, transparent 1px), linear-gradient(90deg, var(--color-teal) 1px, transparent 1px)', backgroundSize: '10% 10%' }}></div>

        <div className="grid grid-cols-[repeat(10,1fr)] gap-[2px] w-[min(calc(100vh-200px),calc(100vw-560px))] aspect-square max-w-[520px] max-h-[520px] z-10">
          {grid.map((rowArr, r) => 
            rowArr.map((val, c) => {
              const {bg, animation, label} = getCellRendering(r, c, val);
              return (
                <div 
                  key={`${r}-${c}`}
                  className={clsx(
                    "aspect-square rounded-sm flex items-center justify-center font-mono-custom text-[9px] font-bold relative cursor-pointer transition-all duration-300 ease-in-out hover:scale-[1.18] hover:z-20 hover:shadow-[0_0_12px_currentColor] border animate-slide-in",
                    bg, animation
                  )}
                  style={{ animationDelay: `${(r * 10 + c) * 3}ms` }}
                >
                  {label}
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="flex items-center justify-center gap-3 px-4 py-2 border-t border-navyBorder bg-navyCard flex-wrap">
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#0A1A28] border border-[#0D2035]"></div>EMPTY</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#2D1A0A] border border-[#4A2A0A]"></div>COLLAPSED</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#3D0A15] border border-[#7A1525]"></div>FIRE</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#2D0A15] border border-danger"></div>CRIT CIV</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#251800] border border-[#4A3000]"></div>INJ CIV</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#0A2510] border border-[#0A4020]"></div>STABLE CIV</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#0A2530] border border-teal"></div>MED UNIT</div>
        <div className="flex items-center gap-1 font-mono-custom text-[9px] text-muted tracking-[1px]"><div className="w-2.5 h-2.5 rounded-[1px] bg-[#1A1A0A] border border-warning"></div>RESC UNIT</div>
      </div>
    </>
  );
}
