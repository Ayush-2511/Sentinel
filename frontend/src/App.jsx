import React from "react"
import { useSocket } from "./hooks/useSocket"
import Grid from "./components/Grid"
import AgentPanels from "./components/AgentPanels"
import VoteHistory from "./components/VoteHistory"
import SurvivalTracker from "./components/SurvivalTracker"
import EventControls from "./components/EventControls"
import ScenarioSelector from "./components/ScenarioSelector"

const MOCK_LOG = [
  { tick: 1, winner: 'CASPER',    action: 'DISPATCH MEDICAL', civId: 1, was_tiebreak: false },
  { tick: 2, winner: 'BALTHASAR', action: 'DISPATCH RESCUE',  civId: 3, was_tiebreak: false },
  { tick: 3, winner: 'MELCHIOR',  action: 'DISPATCH SUPPLY',  civId: null, was_tiebreak: true  },
  { tick: 4, winner: 'CASPER',    action: 'DISPATCH MEDICAL', civId: 2, was_tiebreak: false },
  { tick: 5, winner: 'BALTHASAR', action: 'EVACUATE',         civId: null, was_tiebreak: false },
];

export default function App() {
  const sock = useSocket()

  const tick = sock.gridState?.tick || 0;

  // Build decision log from live vote history, fall back to mock when disconnected
  const decisionLog = sock.voteHistory.length > 0
    ? sock.voteHistory.slice(-5).reverse().map(v => ({
        tick:         v.tick,
        winner:       v.winner,
        action:       v.winning_action?.replace('dispatch_', 'DISPATCH ').toUpperCase() || 'ACTION',
        civId:        v.winning_target_civilian_id ?? null,
        was_tiebreak: v.was_tiebreak,
      }))
    : MOCK_LOG.slice().reverse();

  return (
    <>
      <div className="h-[44px] bg-navyCard border-b border-navyBorder flex items-center justify-between px-4 relative after:content-[''] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[1px] after:bg-gradient-to-r after:from-transparent after:via-teal after:to-transparent after:opacity-40">
        <div className="flex items-center gap-3 cursor-pointer group pl-2">
          {/* Minimalist target reticle */}
          <div className="w-[18px] h-[18px] border-[2px] border-teal flex items-center justify-center transform transition-all duration-500 ease-[cubic-bezier(0.175,0.885,0.32,1.275)] group-hover:rotate-180 group-hover:scale-[1.2] shadow-[0_0_8px_var(--color-teal)]">
            <div className="w-1.5 h-1.5 bg-danger animate-pulse shadow-[0_0_6px_var(--color-danger)]"></div>
          </div>
          
          {/* Split colored syllables */}
          <div className="font-data text-[26px] tracking-[7px] font-bold uppercase transition-all duration-300 mt-[2px] group-hover:tracking-[9px]">
            <span className="text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.6)] group-hover:text-teal transition-colors duration-500">SEN</span>
            <span className="text-teal drop-shadow-[0_0_8px_var(--color-teal)]">TI</span>
            <span className="text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.6)] group-hover:text-teal transition-colors duration-500">NEL</span>
          </div>
        </div>
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-6">
          <div className="flex items-center gap-1.5 font-mono-custom text-[10px] tracking-[2px] text-muted uppercase">
            <div className={`w-1.5 h-1.5 rounded-full ${sock.connected ? "bg-teal shadow-[0_0_8px_var(--color-teal)] animate-pulse-dot" : "bg-danger shadow-[0_0_8px_var(--color-danger)]"}`}></div>
            {sock.connected ? "SYSTEM ONLINE" : "SYSTEM OFFLINE"}
          </div>
          {sock.scenario && (
            <div className="flex items-center gap-1.5 font-mono-custom text-[10px] tracking-[2px] text-muted uppercase">
              <div className="w-1.5 h-1.5 rounded-full bg-danger shadow-[0_0_8px_var(--color-danger)]"></div>
              {sock.scenario} ACTIVE
            </div>
          )}
        </div>
        <div className="flex items-center gap-4 font-mono-custom text-[10px] text-muted tracking-[1px]">
          AGENTS <span className="text-teal">3/3</span> &nbsp;|&nbsp; API <span className="text-teal">OK</span> &nbsp;|&nbsp; TICK <span className="text-teal">{tick}</span>
        </div>
      </div>

      <div className="grid h-[calc(100vh-44px)] gap-0" style={{ gridTemplateColumns: "220px 1fr 300px" }}>

        {/* SIDEBAR */}
        <div className="bg-navyCard border-r border-navyBorder flex flex-col overflow-y-auto overflow-x-hidden">
          <ScenarioSelector onLoad={sock.loadScenario} current={sock.scenario} />

          <>
            <div className="shrink-0 font-mono-custom text-[9px] tracking-[3px] text-muted px-3.5 pt-3.5 pb-1.5 uppercase border-b border-navyBorder mt-2">RESOURCES</div>
            <div className="shrink-0 flex items-center justify-between py-2 px-3.5 border-b border-navyBorder">
              <div className="font-mono-custom text-[9px] text-muted tracking-[1px] flex items-center gap-1.5">
                <span className="text-[11px]">+</span> MEDICAL TEAMS
              </div>
              <div className={`font-data text-[18px] font-bold ${!sock.gridState || sock.gridState.resources?.medical_teams === 0 ? "text-danger" : sock.gridState.resources?.medical_teams < 2 ? "text-warning" : "text-teal"}`}>
                {sock.gridState?.resources?.medical_teams ?? 0}
              </div>
            </div>
            <div className="shrink-0 flex items-center justify-between py-2 px-3.5 border-b border-navyBorder">
              <div className="font-mono-custom text-[9px] text-muted tracking-[1px] flex items-center gap-1.5">
                <span className="text-[11px]">⬡</span> RESCUE UNITS
              </div>
              <div className={`font-data text-[18px] font-bold ${!sock.gridState || sock.gridState.resources?.rescue_units === 0 ? "text-danger" : sock.gridState.resources?.rescue_units < 2 ? "text-warning" : "text-teal"}`}>
                {sock.gridState?.resources?.rescue_units ?? 0}
              </div>
            </div>
            <div className="shrink-0 flex items-center justify-between py-2 px-3.5 border-b border-navyBorder">
              <div className="font-mono-custom text-[9px] text-muted tracking-[1px] flex items-center gap-1.5">
                <span className="text-[11px]">■</span> SUPPLY CACHES
              </div>
              <div className={`font-data text-[18px] font-bold ${!sock.gridState || sock.gridState.resources?.supply_caches === 0 ? "text-danger" : sock.gridState.resources?.supply_caches < 2 ? "text-warning" : "text-teal"}`}>
                {sock.gridState?.resources?.supply_caches ?? 0}
              </div>
            </div>
          </>

          <SurvivalTracker civilians={sock.gridState?.civilians} />

          <EventControls
            onTrigger={sock.triggerEvent}
            onPause={sock.pause}
            onResume={sock.resume}
            onReset={sock.reset}
            isRunning={sock.gridState?.is_running}
          />
        </div>

        {/* CENTER */}
        <div className="flex flex-col bg-navy overflow-hidden">
          <div className="flex items-center justify-between py-2.5 px-4 border-b border-navyBorder bg-navyCard">
            <div className="font-data text-base font-bold tracking-[3px] text-white flex items-center gap-2.5">
              DISASTER GRID
              {sock.gridState?.is_running && (
                <span className="font-mono-custom text-[9px] tracking-[2px] py-0.5 px-2 rounded-sm bg-tealGlow text-teal border border-tealDim animate-blink">● RUNNING</span>
              )}
            </div>

            {/* ── PLAY / PAUSE ── */}
            <div className="flex items-center gap-3">
              {sock.gridState ? (
                sock.gridState.is_running ? (
                  <button
                    onClick={sock.pause}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-sm font-mono-custom text-[9px] tracking-[2px] border border-navyBorder text-muted bg-navyMid hover:border-warning hover:text-warning transition-colors"
                  >
                    <span className="text-[11px]">⏸</span> PAUSE
                  </button>
                ) : (
                  <button
                    onClick={sock.resume}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-sm font-mono-custom text-[9px] tracking-[2px] border border-teal text-teal bg-tealGlow shadow-[0_0_8px_var(--color-teal)] hover:shadow-[0_0_12px_var(--color-teal)] transition-all"
                  >
                    <span className="text-[11px]">▶</span> START SIM
                  </button>
                )
              ) : (
                <button
                  disabled
                  className="flex items-center gap-1.5 px-3 py-1 rounded-sm font-mono-custom text-[9px] tracking-[2px] border border-navyBorder text-muted/40 bg-navyMid cursor-not-allowed opacity-50"
                >
                  <span className="text-[11px]">▶</span> LOAD SCENARIO
                </button>
              )}
              <div className="font-mono-custom text-[11px] text-muted tracking-[2px]">TICK <span className="text-teal">{tick}</span></div>
            </div>
          </div>

          {/* LLM Thinking indicator — visible above the grid while agents deliberate */}
          {sock.agentThinking && sock.agentThinking.status === "thinking" && (
            <div className="shrink-0 flex items-center gap-2 px-4 py-1.5 border-b border-navyBorder bg-[rgba(0,212,184,0.04)]">
              <div className="flex gap-[3px] items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse-dot"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse-dot" style={{animationDelay:"0.2s"}}></span>
                <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse-dot" style={{animationDelay:"0.4s"}}></span>
              </div>
              <span className="font-mono-custom text-[9px] tracking-[2px] text-teal">
                QUERYING{" "}
                <span className="font-bold">
                  {sock.agentThinking.agent === "CASPER"    ? <span className="text-danger">CASPER</span>
                  : sock.agentThinking.agent === "MELCHIOR"  ? <span className="text-warning">MELCHIOR</span>
                  :                                            <span className="text-teal">BALTHASAR</span>}
                </span>
                {" "}— LLM DELIBERATING…
              </span>
            </div>
          )}
          {sock.agentThinking && sock.agentThinking.status === "done" && (
            <div className="shrink-0 flex items-center gap-2 px-4 py-1.5 border-b border-navyBorder bg-[rgba(0,212,184,0.04)]">
              <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
              <span className="font-mono-custom text-[9px] tracking-[2px] text-success">
                {sock.agentThinking.agent} RESPONDED — AWAITING NEXT AGENT
              </span>
            </div>
          )}

          <Grid gridState={sock.gridState} />

          {/* DECISION LOG */}
          <div className="shrink-0 border-t border-navyBorder bg-navyCard" style={{height:'112px'}}>
            <div className="flex items-center justify-between px-4 py-1.5 border-b border-navyBorder">
              <span className="font-mono-custom text-[9px] tracking-[3px] text-muted uppercase">Decision Log</span>
              <span className="font-mono-custom text-[8px] tracking-[2px] text-teal opacity-60">LAST 5 ACTIONS</span>
            </div>
            <div className="overflow-y-auto" style={{height:'80px'}}>
              {decisionLog.map((entry, i) => {
                const agentColor = entry.winner === 'CASPER' ? 'text-danger' : entry.winner === 'MELCHIOR' ? 'text-warning' : 'text-teal';
                const isLatest = i === 0;
                return (
                  <div key={i} className={`flex items-center gap-2 px-4 border-b transition-colors hover:bg-navyMid
                      ${isLatest
                        ? 'py-[5px] bg-[#0A1E2E] border-l-2 border-l-teal border-navyBorder'
                        : 'py-[3px] border-l-2 border-l-transparent border-navyBorder/40 opacity-70'
                      }`}>
                    <span className={`font-mono-custom shrink-0 min-w-[52px] ${isLatest ? 'text-[10px] text-teal' : 'text-[9px] text-muted'}`}>
                      TICK {entry.tick}
                    </span>
                    <span className={`font-mono-custom font-bold shrink-0 min-w-[76px] ${agentColor} ${isLatest ? 'text-[10px]' : 'text-[9px]'}`}>
                      {entry.winner}
                    </span>
                    <span className={`font-mono-custom flex-1 truncate ${isLatest ? 'text-[10px] text-white' : 'text-[9px] text-muted'}`}>
                      {entry.action}{entry.civId ? <span className={isLatest ? ' text-teal font-bold' : ' text-white'}> → CIV #{entry.civId}</span> : ''}
                      {entry.was_tiebreak && <span className="ml-2 text-warning text-[9px]">⚡ TIE</span>}
                    </span>
                    {isLatest && <span className="shrink-0 font-mono-custom text-[8px] text-teal/60 tracking-[1px]">● NEW</span>}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* RIGHT */}
        <div className="bg-navyCard border-l border-navyBorder flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto">
          <AgentPanels
            voteResult={sock.voteResult}
            latestVotes={sock.latestVotes}
            agentThinking={sock.agentThinking}
            agentErrors={sock.agentErrors}
          />
          </div>

          {/* Chart separator */}
          <div className="shrink-0 border-t-2 border-navyBorder relative">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-teal to-transparent opacity-30"></div>
          </div>

          <div className="shrink-0 min-h-[180px] max-h-[240px]">
            <VoteHistory history={sock.voteHistory} />
          </div>
        </div>

      </div>
    </>
  )
}
