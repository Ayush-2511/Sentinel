import React from "react";
import clsx from "clsx";

export default function EventControls({ onTrigger, onPause, onResume, onReset, isRunning }) {
  return (
    <>
      <div className="font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder mt-2">INJECT EVENT</div>
      
      <button 
        className="mx-2.5 my-1 p-2 bg-transparent border border-navyBorder rounded-sm text-muted font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-left w-[calc(100%-20px)] transition-all duration-150 flex items-center gap-2 hover:border-warning hover:text-warning hover:bg-warningDim"
        onClick={() => onTrigger('aftershock')}
      >
        ⚡ AFTERSHOCK
      </button>
      
      <button 
        className="mx-2.5 my-1 p-2 bg-transparent border border-navyBorder rounded-sm text-muted font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-left w-[calc(100%-20px)] transition-all duration-150 flex items-center gap-2 hover:border-danger hover:text-danger hover:bg-dangerDim"
        onClick={() => onTrigger('fire_spread')}
      >
        🔥 FIRE SPREAD
      </button>

      <button 
        className="mx-2.5 my-1 p-2 bg-transparent border border-[#1A3080] rounded-sm text-[#5090FF] font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-left w-[calc(100%-20px)] transition-all duration-150 flex items-center gap-2 hover:border-teal hover:text-teal hover:bg-tealGlow"
        onClick={() => onTrigger('resource_depletion')}
      >
        ■ DEPLETE SUPPLY
      </button>

      <div className="font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder mt-2">CONTROLS</div>
      <div className="grid grid-cols-2 gap-1.5 px-2.5 py-2">
        {isRunning ? (
           <button 
             className="p-2 bg-navyMid border border-navyBorder rounded-sm text-muted font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-center transition-all duration-150 hover:border-teal hover:text-teal"
             onClick={onPause}
           >
             ⏸ PAUSE
           </button>
        ) : (
           <button 
             className="p-2 bg-tealGlow border border-teal rounded-sm text-teal font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-center transition-all duration-150"
             onClick={onResume}
           >
             ▶ RESUME
           </button>
        )}
        <button 
          className="p-2 bg-navyMid border border-navyBorder rounded-sm text-muted font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-center transition-all duration-150 hover:border-teal hover:text-teal"
          onClick={onReset}
        >
          ↺ RESET
        </button>
      </div>
    </>
  );
}
