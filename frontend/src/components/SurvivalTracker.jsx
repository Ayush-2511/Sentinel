import React from "react";

export default function SurvivalTracker({ civilians }) {
  if (!civilians) civilians = [];
  
  const total = civilians.length;
  const aliveItems = civilians.filter(c => c.health > 0);
  const alive = aliveItems.length;
  const dead = total - alive;
  const critical = aliveItems.filter(c => c.health < 30).length;
  
  const survivalRate = total > 0 ? Math.round((alive / total) * 100) : 100;
  
  let barColorClass = "bg-teal shadow-[0_0_6px_var(--color-teal)]";
  if (survivalRate < 40) barColorClass = "bg-danger";
  else if (survivalRate < 75) barColorClass = "bg-warning";

  return (
    <>
      <div className="font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder mt-2">SURVIVAL RATE</div>
      <div className="p-3 border-b border-navyBorder">
        <div className="font-data text-[36px] font-bold text-teal leading-none mb-1">{survivalRate}%</div>
        <div className="font-mono-custom text-[9px] text-muted tracking-[2px] mb-2">CIVILIANS ALIVE</div>
        <div className="h-[3px] bg-navyBorder rounded-[2px] overflow-hidden">
          <div className={`h-full rounded-[2px] transition-[width] duration-800 ease-in-out ${barColorClass}`} style={{ width: `${survivalRate}%` }}></div>
        </div>
        <div className="grid grid-cols-3 gap-1 mt-2">
          <div className="text-center py-1 bg-navyMid border border-navyBorder rounded-sm group">
            <div className="font-data text-[15px] font-bold text-success">{alive}</div>
            <div className="font-mono-custom text-[8px] text-muted tracking-[1px]">ALIVE</div>
          </div>
          <div className="text-center py-1 bg-navyMid border border-navyBorder rounded-sm group">
            <div className="font-data text-[15px] font-bold text-warning">{critical}</div>
            <div className="font-mono-custom text-[8px] text-muted tracking-[1px]">CRIT</div>
          </div>
          <div className="text-center py-1 bg-navyMid border border-navyBorder rounded-sm group">
            <div className="font-data text-[15px] font-bold text-danger">{dead}</div>
            <div className="font-mono-custom text-[8px] text-muted tracking-[1px]">DEAD</div>
          </div>
        </div>
      </div>
    </>
  );
}
