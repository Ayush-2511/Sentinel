import React from "react"
import { useSocket } from "./hooks/useSocket"
import Grid from "./components/Grid"
import AgentPanels from "./components/AgentPanels"
import VoteHistory from "./components/VoteHistory"
import SurvivalTracker from "./components/SurvivalTracker"
import EventControls from "./components/EventControls"
import ScenarioSelector from "./components/ScenarioSelector"

const MOCK_LOG = [
  { tick: 1, winner: 'CASPER',    action: 'DISPATCH MEDICAL',  zone: 'C4', was_tiebreak: false },
  { tick: 2, winner: 'BALTHASAR', action: 'DISPATCH RESCUE',   zone: 'B7', was_tiebreak: false },
  { tick: 3, winner: 'MELCHIOR',  action: 'DISPATCH SUPPLY',   zone: 'D2', was_tiebreak: true  },
  { tick: 4, winner: 'CASPER',    action: 'DISPATCH MEDICAL',  zone: 'A1', was_tiebreak: false },
  { tick: 5, winner: 'BALTHASAR', action: 'EVACUATE',          zone: 'E9', was_tiebreak: false },
];

export default function App() {
  const sock = useSocket()

  const tick = sock.gridState?.tick || 0;

  // Build decision log from live vote history, fall back to mock when disconnected
  const decisionLog = sock.voteHistory.length > 0
    ? sock.voteHistory.slice(-5).reverse().map(v => ({
        tick: v.tick,
        winner: v.winner,
        action: v.votes?.find(x => x.agent === v.winner)?.proposed_action?.replace('dispatch_', 'DISPATCH ').toUpperCase() || 'ACTION',
        zone: v.votes?.find(x => x.agent === v.winner)?.target_zone || '?',
        was_tiebreak: v.was_tiebreak,
      }))
    : MOCK_LOG.slice().reverse();

  return (
    <>
      <div className="h-[44px] bg-navyCard border-b border-navyBorder flex items-center justify-between px-4 relative after:content-[''] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[1px] after:bg-gradient-to-r after:from-transparent after:via-teal after:to-transparent after:opacity-40">
        <div className="font-mono-custom text-base tracking-[6px] text-white flex items-center gap-2.5">
          <span className="text-teal">[</span>SENTINEL<span className="text-teal">]</span>
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
            <div className="font-mono-custom text-[11px] text-muted tracking-[2px]">TICK <span className="text-teal">{tick}</span></div>
          </div>

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
                  <div
                    key={i}
                    className={`flex items-center gap-2 px-4 border-b transition-colors hover:bg-navyMid
                      ${isLatest
                        ? 'py-[5px] bg-[#0A1E2E] border-l-2 border-l-teal border-navyBorder'
                        : 'py-[3px] border-l-2 border-l-transparent border-navyBorder/40 opacity-70'
                      }`}
                  >
                    <span className={`font-mono-custom shrink-0 min-w-[52px] ${isLatest ? 'text-[10px] text-teal' : 'text-[9px] text-muted'}`}>
                      TICK {entry.tick}
                    </span>
                    <span className={`font-mono-custom font-bold shrink-0 min-w-[76px] ${agentColor} ${isLatest ? 'text-[10px]' : 'text-[9px]'}`}>
                      {entry.winner}
                    </span>
                    <span className={`font-mono-custom flex-1 truncate ${isLatest ? 'text-[10px] text-white' : 'text-[9px] text-muted'}`}>
                      {entry.action} → <span className={isLatest ? 'text-teal font-bold' : 'text-white'}>{entry.zone}</span>
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
            <AgentPanels voteResult={sock.voteResult} />
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
