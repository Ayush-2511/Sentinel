import React from 'react';

export default function ResourceLogsModal({ isOpen, onClose, logs }) {
  if (!isOpen) return null;

  return (
    <div className="fixed top-16 right-[320px] z-[9999] w-[600px] bg-navyCard/95 border border-teal/30 shadow-[0_0_20px_rgba(0,0,0,0.8)] flex flex-col max-h-[70vh] backdrop-blur-md rounded-sm">
      <div className="w-full h-full flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-navyBorder bg-navyMid">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-teal animate-pulse-dot shadow-[0_0_8px_var(--color-teal)]"></div>
            <h2 className="font-data text-lg font-bold tracking-[3px] text-white">
              RESOURCE DEPLOYMENT LOGS
            </h2>
          </div>
          <button 
            onClick={onClose}
            className="text-muted hover:text-danger font-mono-custom text-[11px] tracking-[2px] transition-colors"
          >
            [ CLOSE ]
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 bg-[#050D14]/90 custom-scrollbar">
          {logs.length === 0 ? (
            <div className="h-full flex items-center justify-center min-h-[150px]">
              <span className="font-mono-custom text-[10px] tracking-[2px] text-muted/50 uppercase">
                &gt; NO DEPLOYMENT LOGS RECORDED YET
              </span>
            </div>
          ) : (
            <div className="font-mono-custom text-[10px] leading-relaxed space-y-2">
              {logs.slice().reverse().map((log, idx) => {
                const action = log.action.replace('dispatch_', '').toUpperCase();
                const agentColor = log.agent === 'CASPER' ? 'text-danger' : log.agent === 'MELCHIOR' ? 'text-warning' : 'text-teal';
                
                return (
                  <div key={idx} className="border-b border-navyBorder/30 pb-2">
                    <div className="flex items-start gap-2">
                      <span className="text-teal w-14 shrink-0">[T {log.tick}]</span>
                      <span className={`font-bold w-16 shrink-0 ${agentColor}`}>{log.agent}</span>
                      <div className="flex-1 text-white">
                        <span className="text-muted mr-1">&gt;</span>
                        <span className="text-white font-bold">{action}</span>
                        <span className="text-muted mx-1">to</span>
                        <span className="text-teal font-bold">{log.target_id}</span>
                        
                        <div className="mt-1 ml-2 flex flex-wrap gap-3 text-[9px]">
                          <span className="text-muted">
                            REQ: <span className="text-white">{log.amount_requested}</span>
                          </span>
                          <span className="text-muted">
                            SNT: <span className={log.amount_sent > 0 ? "text-success font-bold" : "text-white"}>{log.amount_sent}</span>
                          </span>
                          {log.amount_rejected > 0 && (
                            <span className="text-muted">
                              REJ: <span className="text-danger font-bold">{log.amount_rejected}</span>
                            </span>
                          )}
                        </div>
                        <div className="mt-1 ml-2 text-[9px] text-warning/80">
                          // {log.reason}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
