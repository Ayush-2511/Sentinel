import React from 'react';

export default function VoteHistory({ voteResult }) {
  const method = voteResult?.resolution_method || 'PENDING';

  return (
    <div className="chart-section">
      <div className="chart-title">VOTE HISTORY — LAST 20 TICKS</div>
      <div className="chart-area">
        <div className="sparkline-row">
          <div className="sparkline-label casper">CASPER</div>
          <div className="sparkline">
            <svg viewBox="0 0 200 28" preserveAspectRatio="none">
              <polyline points="0,8 20,6 40,12 60,5 80,4 100,8 120,3 140,7 160,5 180,4 200,3"
                fill="none" stroke="#FF3D5A" strokeWidth="1.5" opacity="0.8" />
            </svg>
          </div>
        </div>
        <div className="sparkline-row">
          <div className="sparkline-label melchior">MELCHIOR</div>
          <div className="sparkline">
            <svg viewBox="0 0 200 28" preserveAspectRatio="none">
              <polyline points="0,18 20,20 40,16 60,22 80,18 100,20 120,15 140,19 160,22 180,18 200,20"
                fill="none" stroke="#FFB020" strokeWidth="1.5" opacity="0.8" />
            </svg>
          </div>
        </div>
        <div className="sparkline-row">
          <div className="sparkline-label balthasar">BALTHASAR</div>
          <div className="sparkline">
            <svg viewBox="0 0 200 28" preserveAspectRatio="none">
              <polyline points="0,12 20,10 40,14 60,8 80,11 100,9 120,12 140,7 160,10 180,8 200,5"
                fill="none" stroke="#00D4B8" strokeWidth="1.5" opacity="0.8" />
            </svg>
          </div>
        </div>
      </div>
      <div className="resolution">
        <div className="res-label">RESOLUTION METHOD</div>
        <div className="res-val">{method.replace('_', ' ')}</div>
      </div>
    </div>
  );
}
