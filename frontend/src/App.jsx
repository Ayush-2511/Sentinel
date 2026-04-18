import React from "react"
import { useSocket } from "./hooks/useSocket"
import Grid from "./components/Grid"
import AgentPanels from "./components/AgentPanels"
import VoteHistory from "./components/VoteHistory"
import SurvivalTracker from "./components/SurvivalTracker"
import EventControls from "./components/EventControls"
import ScenarioSelector from "./components/ScenarioSelector"

export default function App() {
  const sock = useSocket()

  // Fake tick data if no backend connection
  const tick = sock.gridState?.tick || 0;

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

          <VoteHistory history={sock.voteHistory} />
        </div>

        {/* RIGHT */}
        <AgentPanels voteResult={sock.voteResult} />

      </div>
    </>
  )
}
