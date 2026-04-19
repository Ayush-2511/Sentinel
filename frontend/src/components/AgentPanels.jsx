import React from "react";
import clsx from "clsx";

export default function AgentPanels({ voteResult, latestVotes = {}, agentThinking = null, agentErrors = {} }) {
  const defaultAgents = ["CASPER", "MELCHIOR", "BALTHASAR"];

  const agentsData = defaultAgents.map(agentName => {
    // Prefer resolved vote result; fall back to streaming agent_vote data
    const resolvedVote = voteResult?.votes?.find(v => v.agent === agentName);
    const streamVote   = latestVotes[agentName];
    const vote         = resolvedVote ?? streamVote;

    const isWinner   = voteResult?.winner === agentName;
    const isThinking  = agentThinking?.agent === agentName && agentThinking?.status === "thinking";
    const errorInfo   = agentErrors[agentName] ?? null;  // { label, message, code }

    // Action display: backend now sends target_sector (not target_civilian_id)
    let actionText = "AWAITING DATA";
    if (vote) {
      const action = vote.proposed_action?.replace("dispatch_", "DISPATCH ").toUpperCase() || "HOLD";
      const sector = vote.target_sector;
      actionText   = sector ? `${action} → ${sector}` : action;
    }

    return {
      agentName,
      isWinner,
      isThinking,
      errorInfo,
      role:         agentName === "CASPER"    ? "MEDICAL RESPONSE"
                  : agentName === "MELCHIOR"  ? "LOGISTICS & SUPPLY"
                  :                             "RESCUE OPERATIONS",
      action:       actionText,
      score:        vote ? vote.priority_score.toFixed(2) : errorInfo ? "ERR" : "—",
      scorePercent: vote ? `${(vote.priority_score * 100).toFixed(0)}%` : "0%",
      reasoning:    vote ? vote.reasoning : (errorInfo ? errorInfo.message : (isThinking ? "Thinking…" : "…")),
      colorTheme:   agentName === "CASPER" ? "red" : agentName === "MELCHIOR" ? "amber" : "teal",
      nameClass:    agentName === "CASPER" ? "text-danger" : agentName === "MELCHIOR" ? "text-warning" : "text-teal",
    };
  });

  return (
    <div className="flex flex-col overflow-hidden">

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
            agent.isWinner
              ? "before:content-[''] before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[3px]"
              : "hover:bg-[rgba(255,255,255,0.02)]",
            agent.isWinner && agent.colorTheme === "red"   && "bg-[rgba(255,61,90,0.06)]   before:bg-danger",
            agent.isWinner && agent.colorTheme === "amber" && "bg-[rgba(255,176,32,0.06)]  before:bg-warning",
            agent.isWinner && agent.colorTheme === "teal"  && "bg-[rgba(0,212,184,0.06)]   before:bg-teal",
            agent.isThinking && "bg-[rgba(255,255,255,0.03)]"
          )}
        >
          {/* Header row */}
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className={clsx("font-data text-[15px] font-bold tracking-[3px] flex items-center gap-1.5", agent.nameClass)}>
                {agent.agentName}
                {agent.isThinking && (
                  <span className="inline-block w-1.5 h-1.5 rounded-full animate-pulse-dot bg-current" />
                )}
              </div>
              <div className="font-mono-custom text-[8px] text-muted tracking-[1.5px] uppercase">{agent.role}</div>
            </div>

            {agent.isWinner && (
              <div className={clsx(
                "font-mono-custom text-[9px] tracking-[2px] py-1 px-2.5 rounded shadow-lg border animate-pulse-cell",
                agent.colorTheme === "red"   ? "text-danger  border-danger  bg-dangerDim"  :
                agent.colorTheme === "amber" ? "text-warning border-warning bg-warningDim" :
                                               "text-teal   border-teal    bg-tealGlow"
              )}>✓ WINNER</div>
            )}

            {agent.errorInfo && (
              <div className="font-mono-custom text-[8px] tracking-[1px] py-1 px-2 rounded border border-danger/50 bg-dangerDim text-danger max-w-[120px]">
                ⚠ {agent.errorInfo.label}
              </div>
            )}

            {agent.isThinking && !agent.isWinner && !agent.errorInfo && (
              <div className="font-mono-custom text-[8px] text-muted tracking-[2px] animate-pulse">QUERYING LLM…</div>
            )}
          </div>

          {/* Priority score bar */}
          <div className="flex items-center gap-3 mb-2.5">
            <div className="font-mono-custom text-[8.5px] text-muted tracking-[1.5px] w-12">PRIORITY</div>
            <div className="flex-1 h-[3px] bg-navyBorder rounded-[1.5px] overflow-hidden">
              <div
                className={clsx(
                  "h-full rounded-[1.5px] transition-[width] duration-1000 ease-out",
                  agent.colorTheme === "red"   ? "bg-danger  shadow-[0_0_6px_var(--color-danger)]"  :
                  agent.colorTheme === "amber" ? "bg-warning shadow-[0_0_6px_var(--color-warning)]" :
                                                 "bg-teal   shadow-[0_0_6px_var(--color-teal)]"
                )}
                style={{ width: agent.scorePercent }}
              />
            </div>
            <div className={clsx("font-data text-[14px] font-bold min-w-[32px] text-right", agent.nameClass)}>
              {agent.score}
            </div>
          </div>

          {/* Action badge */}
          <div className="font-mono-custom text-[9px] tracking-[1.5px] mb-1.5 px-1.5 py-1 rounded bg-[rgba(0,0,0,0.25)] border border-[rgba(255,255,255,0.05)] inline-block">
            <span className="text-muted">ACTION ➔ </span>
            <span className="text-white font-bold">{agent.action}</span>
          </div>

          {/* Reasoning / Error */}
          <div className={clsx(
            "font-mono-custom text-[9px] leading-relaxed mt-1",
            agent.errorInfo ? "text-danger/80" : "text-muted line-clamp-3",
            agent.isThinking && !agent.errorInfo && "animate-pulse"
          )}>
            {agent.errorInfo
              ? <span title={agent.errorInfo.message}>
                  ⚠ {agent.errorInfo.label}{agent.errorInfo.code === 429 ? " — Rate limit exceeded. Retrying next tick." : " — Agent unavailable."}
                </span>
              : agent.reasoning
            }
          </div>
        </div>
      ))}
    </div>
  );
}
