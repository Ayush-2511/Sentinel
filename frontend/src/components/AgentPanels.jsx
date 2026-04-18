import React from "react";
import clsx from "clsx";

export default function AgentPanels({ voteResult }) {
  const defaultAgents = ["CASPER", "MELCHIOR", "BALTHASAR"];
  
  // Create a normalized list of agents even if voteResult is null
  const agentsData = defaultAgents.map(agentName => {
    const vote = voteResult?.votes?.find(v => v.agent === agentName);
    const isWinner = voteResult?.winner === agentName;
    return {
      agentName,
      isWinner,
      role: agentName === "CASPER" ? "MEDICAL RESPONSE" : agentName === "MELCHIOR" ? "LOGISTICS & SUPPLY" : "RESCUE OPERATIONS",
      action: vote ? `${vote.proposed_action.replace("dispatch_", "DISPATCH ")} @ ${vote.target_zone || 'NONE'}`.toUpperCase() : "AWAITING DATA",
      score: vote ? vote.priority_score.toFixed(2) : "0.00",
      scorePercent: vote ? `${vote.priority_score * 100}%` : "0%",
      reasoning: vote ? vote.reasoning : "...",
      colorTheme: agentName === "CASPER" ? "red" : agentName === "MELCHIOR" ? "amber" : "teal",
      nameClass: agentName === "CASPER" ? "text-danger" : agentName === "MELCHIOR" ? "text-warning" : "text-teal",
    };
  });

  return (
    <div className="bg-navyCard border-l border-navyBorder flex flex-col overflow-hidden h-[calc(100vh-44px)]">
      
      {voteResult?.was_tiebreak && (
        <div className="flex items-center gap-1.5 py-1.5 px-3 bg-warningDim border-b border-warning/20 font-mono-custom text-[9px] text-warning tracking-[2px] shrink-0">
          ⚡ SPLIT VOTE — TIEBREAK ACTIVE
        </div>
      )}

      {agentsData.map((agent, index) => (
        <div 
          key={agent.agentName}
          className={clsx(
            "border-b border-navyBorder py-3 px-4 transition-all duration-300 relative shrink-0",
            agent.isWinner ? "bg-gradient-to-r from-[rgba(0,212,184,0.08)] to-transparent before:content-[''] before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[3px] before:shadow-[0_0_8px_currentColor]" : "hover:bg-[rgba(255,255,255,0.02)]",
            agent.isWinner && agent.colorTheme === "red" && "before:bg-danger from-[rgba(255,61,90,0.08)] before:text-danger",
            agent.isWinner && agent.colorTheme === "amber" && "before:bg-warning from-[rgba(255,176,32,0.08)] before:text-warning",
            agent.isWinner && agent.colorTheme === "teal" && "before:bg-teal before:text-teal"
          )}
          style={{ animation: `slide-in 0.4s ease-out forwards ${index * 0.15}s`, opacity: 0 }}
        >
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className={clsx("font-data text-[15px] font-bold tracking-[3px] drop-shadow-md", agent.nameClass)}>{agent.agentName}</div>
              <div className="font-mono-custom text-[8px] text-muted tracking-[1.5px] uppercase">{agent.role}</div>
            </div>
            {agent.isWinner && (
              <div className={clsx(
                "font-mono-custom text-[9px] tracking-[2px] py-1 px-2.5 rounded shadow-lg border animate-pulse-cell",
                agent.colorTheme === "red" ? "text-danger border-danger bg-dangerDim" : 
                agent.colorTheme === "amber" ? "text-warning border-warning bg-warningDim" : 
                "text-teal border-teal bg-tealGlow"
              )}>✓ WINNER</div>
            )}
          </div>
          
          <div className="flex items-center gap-3 mb-2.5">
            <div className="font-mono-custom text-[8.5px] text-muted tracking-[1.5px] w-12">PRIORITY</div>
            <div className="flex-1 h-[3px] bg-navyBorder rounded-[1.5px] overflow-hidden drop-shadow-md">
              <div 
                className={clsx(
                  "h-full rounded-[1.5px] transition-[width] duration-1000 ease-out",
                  agent.colorTheme === "red" ? "bg-danger shadow-[0_0_6px_var(--color-danger)]" : 
                  agent.colorTheme === "amber" ? "bg-warning shadow-[0_0_6px_var(--color-warning)]" : 
                  "bg-teal shadow-[0_0_6px_var(--color-teal)]"
                )}
                style={{ width: agent.scorePercent }}
              ></div>
            </div>
            <div className={clsx("font-data text-[14px] font-bold min-w-[32px] text-right drop-shadow", agent.nameClass)}>
              {agent.score}
            </div>
          </div>

          <div className="font-mono-custom text-[9px] tracking-[1.5px] mb-1.5 p-1.5 rounded bg-[rgba(0,0,0,0.2)] border border-[rgba(255,255,255,0.05)] inline-block">
            <span className="text-muted">ACTION ➔ </span>
            <span className="text-white font-bold drop-shadow-sm">{agent.action}</span>
          </div>

          <div className="font-mono-custom text-[9px] text-muted leading-relaxed line-clamp-3 mt-1">
            {agent.reasoning}
          </div>
        </div>
      ))}

    </div>
  );
}
