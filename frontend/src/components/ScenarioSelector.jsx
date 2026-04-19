import React, { useState, useRef, useEffect } from "react";
import clsx from "clsx";

export default function ScenarioSelector({ onLoad, current }) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  const scenarios = [
    { id: "city_fire", name: "URBAN FIRE", icon: "🔥", severity: "CRITICAL", sClass: "text-danger" },
    { id: "earthquake", name: "EARTHQUAKE", icon: "🏚️", severity: "HIGH", sClass: "text-warning" },
    { id: "flood", name: "FLOOD", icon: "🌊", severity: "HIGH", sClass: "text-warning" },
    { id: "building_collapse", name: "BUILDING COLLAPSE", icon: "🏗️", severity: "MEDIUM", sClass: "text-teal" },
  ];

  const activeScen = scenarios.find(s => s.id === current) || { name: "SELECT MISSION", icon: "⚙️" };

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="px-3.5 py-3 border-b border-navyBorder bg-navyMid/30 relative" ref={containerRef}>
      <div className="font-mono-custom text-[8px] tracking-[3px] text-muted uppercase mb-2">Operation Selection</div>
      
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={clsx(
            "w-full bg-navy border rounded-[3px] py-2.5 px-3 flex items-center justify-between transition-all",
            isOpen ? "border-teal shadow-[0_0_12px_var(--color-teal)]" : "border-navyBorder hover:border-teal/50"
          )}
        >
          <div className="flex items-center gap-2.5">
            <span className="text-[14px]">{activeScen.icon}</span>
            <span className="font-data text-[13px] font-bold tracking-[2px] text-white uppercase">{activeScen.name}</span>
          </div>
          <span className={clsx("text-[10px] transition-transform duration-300", isOpen && "rotate-180")}>▼</span>
        </button>

        {/* Custom Dropdown Menu */}
        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1.5 bg-navyCard border border-teal/40 rounded-[3px] shadow-[0_8px_24px_rgba(0,0,0,0.8)] z-[2000] overflow-hidden backdrop-blur-md animate-slide-in">
            {scenarios.map((scen) => (
              <div
                key={scen.id}
                onClick={() => {
                  onLoad(scen.id);
                  setIsOpen(false);
                }}
                className={clsx(
                  "px-4 py-3 flex items-center justify-between cursor-pointer transition-colors group",
                  current === scen.id ? "bg-tealGlow" : "hover:bg-[rgba(255,255,255,0.03)]"
                )}
              >
                <div className="flex items-center gap-3">
                  <span className="text-[16px] group-hover:scale-125 transition-transform">{scen.icon}</span>
                  <div>
                    <div className={clsx("font-data text-[12px] font-bold tracking-[1.5px]", current === scen.id ? "text-teal" : "text-white")}>
                      {scen.name}
                    </div>
                  </div>
                </div>
                <div className={clsx("font-mono-custom text-[8px] tracking-[1px] py-0.5 px-1.5 border rounded-[2px]", 
                  scen.severity === "CRITICAL" ? "border-danger/30 text-danger" : 
                  scen.severity === "HIGH" ? "border-warning/30 text-warning" : "border-teal/30 text-teal"
                )}>
                  {scen.severity}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {current && (
        <div className="mt-2.5 flex items-center justify-between opacity-80">
          <span className="font-mono-custom text-[8px] text-muted tracking-[1px] uppercase">
            STATUS: <span className="text-teal font-bold animate-blink">ACTIVE</span>
          </span>
          <span className={clsx("font-mono-custom text-[8px] tracking-[1px] uppercase", activeScen.sClass)}>
             LIMITS: NOMINAL
          </span>
        </div>
      )}
    </div>
  );
}
