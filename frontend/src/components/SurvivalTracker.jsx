import React from 'react';

export default function SurvivalTracker({ state }) {
  const resources = state?.resources || { medical_teams: 0, rescue_units: 0, supply_caches: 0 };
  const civilians = state?.civilians || [];
  
  const alive = civilians.filter(c => c.health > 0).length;
  const dead = civilians.filter(c => c.health <= 0).length;
  const crit = civilians.filter(c => c.health > 0 && c.status === 'critical').length;
  const survivalRate = state?.survival_rate !== undefined ? state.survival_rate * 100 : 0;
  
  const barClass = survivalRate > 60 ? 'teal' : survivalRate > 40 ? 'amber' : 'red';

  return (
    <>
      <div className="section-label">RESOURCES</div>

      <div className="resource-row">
        <div className="resource-label"><span className="resource-icon">+</span> MEDICAL TEAMS</div>
        <div className={`resource-value ${resources.medical_teams === 0 ? 'depleted' : resources.medical_teams === 1 ? 'low' : ''}`}>
          {resources.medical_teams}
        </div>
      </div>
      <div className="resource-row">
        <div className="resource-label"><span className="resource-icon">⬡</span> RESCUE UNITS</div>
        <div className={`resource-value ${resources.rescue_units === 0 ? 'depleted' : resources.rescue_units === 1 ? 'low' : ''}`}>
          {resources.rescue_units}
        </div>
      </div>
      <div className="resource-row">
        <div className="resource-label"><span className="resource-icon">■</span> SUPPLY CACHES</div>
        <div className={`resource-value ${resources.supply_caches === 0 ? 'depleted' : resources.supply_caches === 1 ? 'low' : ''}`}>
          {resources.supply_caches}
        </div>
      </div>

      <div className="section-label">SURVIVAL RATE</div>
      <div className="survival-block">
        <div className="survival-number">{Math.round(survivalRate)}%</div>
        <div className="survival-label">CIVILIANS ALIVE</div>
        <div className="bar-track">
          <div className={`bar-fill ${barClass}`} style={{ width: `${Math.round(survivalRate)}%` }}></div>
        </div>
        <div className="survival-stats">
          <div className="stat-cell g"><div className="stat-num">{alive}</div><div className="stat-name">ALIVE</div></div>
          <div className="stat-cell a"><div className="stat-num">{crit}</div><div className="stat-name">CRIT</div></div>
          <div className="stat-cell r"><div className="stat-num">{dead}</div><div className="stat-name">DEAD</div></div>
        </div>
      </div>
    </>
  );
}
