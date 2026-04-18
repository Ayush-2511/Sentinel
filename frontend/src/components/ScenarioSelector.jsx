import React from "react";
import clsx from "clsx";

export default function ScenarioSelector({ onLoad, current }) {
  const scenarios = [
    { id: "earthquake", name: "EARTHQUAKE", meta: "12 CIV · 5 COLLAPSED ZONES", severity: "HIGH", severityClass: "text-danger bg-dangerDim border-danger/30", colorTheme: "red" },
    { id: "flood", name: "FLOOD", meta: "8 CIV · RISING WATER ZONES", severity: "MED", severityClass: "text-warning bg-warningDim border-warning/30", colorTheme: "amber" },
    { id: "building_collapse", name: "BUILDING COLLAPSE", meta: "6 CIV · DENSE RUBBLE ZONES", severity: "CRITICAL", severityClass: "text-danger bg-dangerDim border-danger/30", colorTheme: "red" }
  ];

  return (
    <>
      <div className="font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder">SCENARIOS</div>
      {scenarios.map(scen => {
        const isActive = current ? current === scen.id : scen.id === "earthquake";
        
        let activeHoverClass = "hover:border-tealDim hover:bg-tealGlow before:bg-transparent";
        let activeClass = "";
        
        if (isActive) {
          activeClass = "border-tealDim bg-tealGlow before:bg-teal";
          if (scen.colorTheme === "red") activeClass = "border-danger/50 bg-danger/10 before:bg-danger";
          if (scen.colorTheme === "amber") activeClass = "border-warning/50 bg-warning/10 before:bg-warning";
        }

        return (
          <div 
            key={scen.id} 
            className={clsx(
              "mx-2.5 my-2 p-2.5 border border-navyBorder rounded-[3px] cursor-pointer transition-all duration-150 relative overflow-hidden group before:content-[''] before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[2px] hover:before:bg-teal",
              activeHoverClass,
              isActive && activeClass
            )}
            onClick={() => onLoad(scen.id)}
          >
            <div className="font-data text-[13px] font-bold tracking-[1px] text-white mb-[3px]">{scen.name}</div>
            <div className="font-mono-custom text-[9px] text-muted tracking-[1px]">{scen.meta}</div>
            <div>
              <span className={clsx("inline-block font-mono-custom text-[8px] py-[1px] px-[5px] rounded-[2px] mt-1 tracking-[1px] border", scen.severityClass)}>
                SEVERITY: {scen.severity}
              </span>
            </div>
          </div>
        );
      })}
    </>
  );
}
