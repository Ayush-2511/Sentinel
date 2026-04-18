import React from 'react';

// From the wireframe definitions:
// 0 = empty
// 1 = collapsed building
// 2 = fire
// 3 = civilian (details in civilians array)
// 4 = resource cache
// 5 = active unit

function getCellInfo(val, rowIndex, colIndex, state) {
  let cls = 'c-empty';
  let label = '';

  if (val === 1) {
    cls = 'c-collapsed';
    label = '';
  } else if (val === 2) {
    cls = 'c-fire';
    label = '';
  } else if (val === 3) {
    // Find the civilian
    const civ = state?.civilians?.find(c => c.pos[0] === rowIndex && c.pos[1] === colIndex && c.health > 0);
    if (civ) {
      if (civ.status === 'critical') {
        cls = 'c-critical';
      } else if (civ.status === 'stable') {
        cls = 'c-stable';
      } else {
        cls = 'c-injured';
      }
      label = civ.id.toString();
    }
  } else if (val === 4) {
    cls = 'c-resource';
    label = '';
  } else if (val === 5) {
    // Find the unit
    const unit = state?.active_units?.find(u => u.pos[0] === rowIndex && u.pos[1] === colIndex);
    if (unit) {
      if (unit.type === 'medical') {
        cls = 'c-unit-med';
        label = '+';
      } else if (unit.type === 'rescue') {
        cls = 'c-unit-resc';
        label = 'R';
      } else {
        cls = 'c-unit-med'; // fallback
      }
    }
  }

  return { cls, label };
}

export default function Grid({ state }) {
  const isRunning = state ? state.is_running : false;
  const tick = state ? state.tick : 0;
  
  // Default 10x10 empty grid if state is missing
  const grid = state?.grid || Array(10).fill(Array(10).fill(0));

  return (
    <div className="center">
      <div className="grid-header">
        <div className="grid-title">
          DISASTER GRID
          <span className={`running-badge ${!isRunning ? 'paused' : ''}`}>
            {isRunning ? '● RUNNING' : '● PAUSED'}
          </span>
        </div>
        <div className="tick-display">TICK <span>{tick}</span></div>
      </div>

      <div className="grid-wrap">
        <div className="corner tl"></div>
        <div className="corner tr"></div>
        <div className="corner bl"></div>
        <div className="corner br"></div>
        <div className="grid-board">
          {grid.map((row, rowIndex) =>
            row.map((val, colIndex) => {
              const { cls, label } = getCellInfo(val, rowIndex, colIndex, state);
              return (
                <div key={`${rowIndex}-${colIndex}`} className={`cell ${cls}`}>
                  {label}
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="legend">
        <div className="legend-item"><div className="legend-dot" style={{ background: '#0A1A28', border: '1px solid #0D2035' }}></div>EMPTY</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#2D1A0A', border: '1px solid #4A2A0A' }}></div>COLLAPSED</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#3D0A15', border: '1px solid #7A1525' }}></div>FIRE</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#2D0A15', border: '1px solid #FF3D5A' }}></div>CRITICAL CIV</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#251800', border: '1px solid #4A3000' }}></div>INJURED CIV</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#0A2510', border: '1px solid #0A4020' }}></div>STABLE CIV</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#0A2530', border: '1px solid #00D4B8' }}></div>MED UNIT</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#1A1A0A', border: '1px solid #FFB020' }}></div>RESCUE UNIT</div>
      </div>

      <div className="decision-log">
        <div className="log-header">DECISION LOG</div>
        <div id="log-feed">
          {state?.events?.map((ev, i) => (
            <div key={i} className="log-entry">
              <span className="log-tick">T-{tick}</span>
              <span className="log-agent" style={{ color: '#FFB020', minWidth: '70px' }}>SYSTEM</span>
              <span className="log-text">Event injected: {ev}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
