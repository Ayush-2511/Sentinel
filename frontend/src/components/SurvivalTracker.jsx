import React from "react";

export default function SurvivalTracker({ totalCivilians }) {
  const tc = totalCivilians || {};
  const total = tc.total || 0;
  const critical = tc.critical || 0;
  const stable = tc.stable || 0;
  const rescued = tc.rescued || 0;
  const alive = critical + stable + rescued;
  const dead = Math.max(0, total - alive);

  const survivalRate = total > 0 ? Math.round((alive / total) * 100) : 0;

  let barColorClass = "bg-teal shadow-[0_0_6px_var(--color-teal)]";
  let rateColorClass = "text-teal drop-shadow-[0_0_8px_rgba(0,212,184,0.5)]";

  if (survivalRate < 40) {
    barColorClass = "bg-danger shadow-[0_0_6px_var(--color-danger)]";
    rateColorClass = "text-danger drop-shadow-[0_0_8px_rgba(255,61,90,0.5)]";
  } else if (survivalRate < 75) {
    barColorClass = "bg-warning shadow-[0_0_6px_var(--color-warning)]";
    rateColorClass = "text-warning drop-shadow-[0_0_8px_rgba(255,176,32,0.5)]";
  }

  return (
    <>
      <div className="shrink-0 font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder mt-2">SURVIVAL RATE</div>
      <div className="shrink-0 p-3 border-b border-navyBorder">
        <div className={`font-data text-[48px] font-bold leading-none mb-1 ${rateColorClass}`}>{survivalRate}%</div>
        <div className="font-mono-custom text-[9px] text-muted tracking-[2px] mb-2">CIVILIANS ALIVE</div>
        <div className="h-[3px] bg-navyBorder rounded-[2px] overflow-hidden">
          <div className={`h-full rounded-[2px] transition-[width] duration-800 ease-in-out ${barColorClass}`} style={{ width: `${survivalRate}%` }}></div>
        </div>
        <div className="grid grid-cols-4 gap-1 mt-2">
          <div className="text-center py-1 bg-navyMid border border-navyBorder rounded-sm">
            <div className="font-data text-[16px] font-bold text-danger">{critical}</div>
            <div className="font-mono-custom text-[8px] text-muted tracking-[1px]">CRIT</div>
          </div>
          <div className="text-center py-1 bg-navyMid border border-navyBorder rounded-sm">
            <div className="font-data text-[16px] font-bold text-warning">{stable}</div>
            <div className="font-mono-custom text-[8px] text-muted tracking-[1px]">STBL</div>
          </div>
          <div className="text-center py-1 bg-navyMid border border-navyBorder rounded-sm">
            <div className="font-data text-[16px] font-bold text-success">{rescued}</div>
            <div className="font-mono-custom text-[8px] text-muted tracking-[1px]">RESC</div>
          </div>
          <div className="text-center py-1 bg-navyMid border border-navyBorder rounded-sm">
            <div className="font-data text-[16px] font-bold text-danger">{dead}</div>
            <div className="font-mono-custom text-[8px] text-muted tracking-[1px]">DEAD</div>
          </div>
        </div>
      </div>
    </>
  );
}
