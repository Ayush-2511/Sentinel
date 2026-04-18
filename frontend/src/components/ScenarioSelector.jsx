import React from 'react';
import clsx from 'clsx';

export default function ScenarioSelector({ activeScenario, onLoadScenario }) {
  const scenarios = [
    {
      id: 'earthquake',
      name: 'EARTHQUAKE',
      meta: '12 CIV · 5 COLLAPSED ZONES',
      severity: 'HIGH',
      colorClass: 'red',
    },
    {
      id: 'flood',
      name: 'FLOOD',
      meta: '8 CIV · RISING WATER ZONES',
      severity: 'MED',
      colorClass: 'amber',
    },
    {
      id: 'building_collapse',
      name: 'BUILDING COLLAPSE',
      meta: '6 CIV · DENSE RUBBLE ZONES',
      severity: 'CRITICAL',
      colorClass: 'red',
    },
  ];

  return (
    <>
      <div className="section-label">SCENARIOS</div>
      {scenarios.map((s) => {
        const isActive = activeScenario === s.id;
        const color = s.colorClass;
        return (
          <div
            key={s.id}
            className={clsx(
              'scenario-card',
              isActive && 'active',
              isActive && `active-${color}`
            )}
            onClick={() => onLoadScenario(s.id)}
          >
            <div className="scenario-name">{s.name}</div>
            <div className="scenario-meta">{s.meta}</div>
            <div>
              <span className={`scenario-badge badge-${color}`}>
                SEVERITY: {s.severity}
              </span>
            </div>
          </div>
        );
      })}
    </>
  );
}
