import React from 'react';
import { useSocket } from './hooks/useSocket';
import ScenarioSelector from './components/ScenarioSelector';
import EventControls from './components/EventControls';
import SurvivalTracker from './components/SurvivalTracker';
import Grid from './components/Grid';
import AgentPanels from './components/AgentPanels';
import VoteHistory from './components/VoteHistory';

function App() {
  const {
    isConnected,
    stateUpdate,
    voteResult,
    activeScenario,
    loadScenario,
    triggerEvent,
    pause,
    resume,
    reset,
  } = useSocket();

  const isRunning = stateUpdate?.is_running || false;

  return (
    <>
      <div className="topbar">
        <div className="logo">
          <span className="logo-bracket">[</span>SENTINEL<span className="logo-bracket">]</span>
        </div>
        <div className="topbar-center">
          <div className="status-pill">
            <div className={`status-dot ${!isConnected ? 'red' : ''}`} style={!isConnected ? {background:'#FF3D5A', boxShadow:'0 0 8px #FF3D5A', animation:'none'} : {}}></div>
            {isConnected ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
          </div>
          {activeScenario && (
            <div className="status-pill">
              <div className="status-dot red" style={{background:'#FF3D5A', boxShadow:'0 0 8px #FF3D5A', animation:'none'}}></div>
              {activeScenario.toUpperCase()} ACTIVE
            </div>
          )}
        </div>
        <div className="topbar-right">
          AGENTS <span>3/3</span> &nbsp;|&nbsp; API <span>OK</span> &nbsp;|&nbsp; SOCKET <span>{isConnected ? 'CONNECTED' : 'DISCONNECTED'}</span>
        </div>
      </div>

      <div className="main-layout">
        <div className="sidebar">
          <ScenarioSelector activeScenario={activeScenario} onLoadScenario={loadScenario} />
          <SurvivalTracker state={stateUpdate} />
          <EventControls 
            onTriggerEvent={triggerEvent} 
            isRunning={isRunning} 
            onPause={pause} 
            onResume={resume} 
            onReset={reset} 
          />
        </div>

        <Grid state={stateUpdate} />

        <div className="right">
          <AgentPanels voteResult={voteResult} />
          <VoteHistory voteResult={voteResult} />
        </div>
      </div>
    </>
  );
}

export default App;
