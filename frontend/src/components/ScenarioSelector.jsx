import React from "react";
import clsx from "clsx";

export default function ScenarioSelector({ onLoad, current }) {
  const scenarios = [
    {
      id: "city_fire",
      name: "URBAN FIRE",
      meta: "6 BLOCKS · 3 BURNING · FIRE SPREADING",
      severity: "CRITICAL",
      severityClass: "text-danger bg-dangerDim border-danger/30",
      icon: "🔥",
    },
    {
      id: "earthquake",
      name: "EARTHQUAKE",
      meta: "12 SECTORS · STRUCTURAL COLLAPSE",
      severity: "HIGH",
      severityClass: "text-warning bg-warningDim border-warning/30",
      icon: "🏚️",
    },
    {
      id: "flood",
      name: "FLOOD",
      meta: "12 SECTORS · GOMTI RIVER OVERFLOW",
      severity: "HIGH",
      severityClass: "text-warning bg-warningDim border-warning/30",
      icon: "🌊",
    },
    {
      id: "building_collapse",
      name: "BUILDING COLLAPSE",
      meta: "12 SECTORS · HIGH RESCUE DEMAND",
      severity: "MEDIUM",
      severityClass: "text-teal bg-tealGlow border-teal/30",
      icon: "🏗️",
    },
  ];

  return (
    <>
      <div className="shrink-0 font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder">SCENARIOS</div>
      {scenarios.map(scen => {
        const isActive = current === scen.id;
        const colorAccent = scen.severity === "CRITICAL" ? "danger" : scen.severity === "HIGH" ? "warning" : "teal";

        return (
          <div
            key={scen.id}
            className={clsx(
              "shrink-0 mx-2.5 my-1.5 p-2.5 border rounded-[3px] cursor-pointer transition-all duration-150 relative overflow-hidden group",
              "before:content-[''] before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[2px]",
              isActive
                ? `border-${colorAccent}/50 bg-${colorAccent}/10 before:bg-${colorAccent} shadow-[0_0_8px_rgba(255,61,90,0.12)]`
                : "border-navyBorder hover:border-teal/30 hover:bg-teal/5 hover:before:bg-teal/50 before:bg-transparent"
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
