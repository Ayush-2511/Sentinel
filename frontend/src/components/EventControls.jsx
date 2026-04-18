import React from 'react';

export default function EventControls({ onTriggerEvent, isRunning, onPause, onResume, onReset }) {
  return (
    <>
      <div className="section-label">INJECT EVENT</div>
      <button className="event-btn" onClick={() => onTriggerEvent('aftershock')}>
        ⚡ AFTERSHOCK
      </button>
      <button className="event-btn red" onClick={() => onTriggerEvent('fire_spread')}>
        🔥 FIRE SPREAD
      </button>
      <button
        className="event-btn"
        style={{ color: '#5090FF', borderColor: '#1A3080' }}
        onClick={() => onTriggerEvent('resource_depletion')}
      >
        ■ DEPLETE SUPPLY
      </button>

      <div className="section-label">CONTROLS</div>
      <div className="ctrl-row">
        <button
          className={`ctrl-btn ${isRunning ? 'active' : ''}`}
          onClick={isRunning ? onPause : onResume}
        >
          {isRunning ? '⏸ PAUSE' : '▶ RESUME'}
        </button>
        <button className="ctrl-btn" onClick={onReset}>
          ↺ RESET
        </button>
      </div>
    </>
  );
}
