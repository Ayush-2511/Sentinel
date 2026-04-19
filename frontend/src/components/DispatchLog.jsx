import React from "react";

export default function DispatchLog({ history = [], onClose }) {
  return (
    <div className="flex flex-col h-full bg-navy/95 backdrop-blur-md border border-tealDim shadow-[0_0_40px_rgba(0,0,0,0.8)] tactical-bg">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-navyBorder bg-navyMid/50">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-teal shadow-[0_0_10px_var(--color-teal)]"></div>
          <span className="font-data text-lg tracking-[4px] text-white uppercase font-bold">Resource Deployment Logs</span>
        </div>
        <button 
          onClick={onClose}
          className="font-mono-custom text-[10px] text-teal hover:text-white tracking-[2px] transition-colors uppercase flex items-center gap-2"
        >
          [ CLOSE ]
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 bg-navyCard/40">
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 opacity-20">
            <div className="font-mono-custom text-xs tracking-[4px] text-muted uppercase">System idle — No active dispatches recorded</div>
          </div>
        ) : (
          history.map((entry, idx) => {
            const agentColor = 
              entry.agent === 'CASPER' ? 'text-danger' : 
              entry.agent === 'MELCHIOR' ? 'text-warning' : 'text-teal';
            
            return (
              <div 
                key={`${entry.tick}-${idx}`} 
                className="group border-b border-navyBorder/40 pb-5 last:border-0"
              >
                <div className="flex items-center gap-6 mb-2">
                  <span className="font-mono-custom text-[11px] text-teal w-12 tracking-[1px] font-bold">
                    [T {entry.tick}]
                  </span>
                  
                  <span className={`font-mono-custom text-[11px] font-black uppercase tracking-[2px] w-24 ${agentColor}`}>
                    {entry.agent}
                  </span>
                  
                  <div className="flex items-center gap-2 font-mono-custom text-[11px]">
                    <span className="text-muted/60">&gt;</span>
                    <span className="text-white font-bold">{entry.action}</span>
                    <span className="text-muted/60">to</span>
                    <span className="text-teal font-bold tracking-[1px]">{entry.target}</span>
                  </div>
                </div>

                <div className="flex items-center gap-8 pl-[72px] mb-2 font-mono-custom text-[9px] tracking-[1.5px]">
                  <div className="flex gap-2">
                    <span className="text-muted uppercase">Req:</span>
                    <span className="text-white font-bold">{entry.req}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-muted uppercase">Snt:</span>
                    <span className={`font-bold ${entry.snt > 0 ? 'text-success' : 'text-muted'}`}>{entry.snt}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-muted uppercase">Rej:</span>
                    <span className={`font-bold ${entry.rej > 0 ? 'text-danger' : 'text-muted'}`}>{entry.rej}</span>
                  </div>
                </div>

                <div className="pl-[72px] font-mono-custom text-[9px] text-muted/60 italic leading-relaxed">
                  // {entry.reason}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
