import React from "react";
import clsx from "clsx";

export default function ScenarioSelector({ onLoad, current }) {
  // Only the fire scenario for now
  const scenarios = [
    {
      id: "simple_crisis",
      name: "ISOLATED BUILDING FIRE",
      meta: "3 CIV · 1 FIRE SOURCE · 3×3 BUILDING",
      severity: "HIGH",
      severityClass: "text-danger bg-dangerDim border-danger/30",
      colorTheme: "red",
      icon: "🔥",
    },
  ];

  return (
    <>
      <div className="shrink-0 font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder">SCENARIOS</div>
      {scenarios.map(scen => {
        const isActive = current === scen.id || (!current && scen.id === "simple_crisis");

        return (
          <div
            key={scen.id}
            className={clsx(
              "shrink-0 mx-2.5 my-2 p-2.5 border rounded-[3px] cursor-pointer transition-all duration-150 relative overflow-hidden group",
              "before:content-[''] before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[2px]",
              isActive
                ? "border-danger/50 bg-danger/10 before:bg-danger shadow-[0_0_8px_rgba(255,61,90,0.12)]"
                : "border-navyBorder hover:border-danger/30 hover:bg-danger/5 hover:before:bg-danger/50 before:bg-transparent"
            )}
            onClick={() => onLoad(scen.id)}
          >
            <div className="flex items-center gap-1.5 mb-[3px]">
              <span className="text-[13px]">{scen.icon}</span>
              <div className="font-data text-[12px] font-bold tracking-[1px] text-white">{scen.name}</div>
            </div>
            <div className="font-mono-custom text-[9px] text-muted tracking-[1px] mb-1">{scen.meta}</div>
            <div className="flex items-center gap-2">
              <span className={clsx("inline-block font-mono-custom text-[8px] py-[1px] px-[5px] rounded-[2px] tracking-[1px] border", scen.severityClass)}>
                SEVERITY: {scen.severity}
              </span>
              {isActive && (
                <span className="font-mono-custom text-[8px] text-teal tracking-[1px]">● LOADED</span>
              )}
            </div>
          </div>
        );
      })}
    </>
  );
}
