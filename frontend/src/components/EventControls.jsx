import React from "react";
import clsx from "clsx";

export default function EventControls({ onPause, onResume, onReset, isRunning }) {
  return (
    <>
      <div className="shrink-0 font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder mt-2">SIMULATION</div>
      <div className="px-2.5 py-2 flex flex-col gap-1.5">
        {isRunning ? (
          <button
            className="p-2 bg-navyMid border border-navyBorder rounded-sm text-muted font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-center transition-all duration-150 hover:border-warning hover:text-warning hover:bg-warningDim w-full"
            onClick={onPause}
          >
            ⏸ PAUSE SIMULATION
          </button>
        ) : (
          <button
            className="p-2 bg-tealGlow border border-teal rounded-sm text-teal font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-center transition-all duration-150 shadow-[0_0_8px_var(--color-teal)] hover:shadow-[0_0_12px_var(--color-teal)] w-full"
            onClick={onResume}
          >
            ▶ START / RESUME
          </button>
        )}
        <button
          className="p-2 bg-navyMid border border-navyBorder rounded-sm text-muted font-mono-custom text-[9px] tracking-[2px] cursor-pointer text-center transition-all duration-150 hover:border-danger hover:text-danger hover:bg-dangerDim w-full"
          onClick={onReset}
        >
          ↺ RESET
        </button>
      </div>
    </>
  );
}
