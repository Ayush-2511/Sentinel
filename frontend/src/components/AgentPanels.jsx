import React from 'react';

const agentDetails = {
  CASPER: { name: 'CASPER', role: 'MEDICAL RESPONSE', cls: 'casper' },
  MELCHIOR: { name: 'MELCHIOR', role: 'LOGISTICS & SUPPLY', cls: 'melchior' },
  BALTHASAR: { name: 'BALTHASAR', role: 'RESCUE OPERATIONS', cls: 'balthasar' },
};

export default function AgentPanels({ voteResult }) {
  if (!voteResult || !voteResult.votes) {
    return (
      <>
        {Object.values(agentDetails).map(agent => (
          <div key={agent.name} className={`agent-card ${agent.cls}`}>
            <div className="agent-head">
              <div>
                <div className={`agent-name ${agent.cls}`}>{agent.name}</div>
                <div className="agent-role">{agent.role}</div>
              </div>
            </div>
            <div className="agent-reasoning" style={{ marginTop: '10px' }}>Waiting for data...</div>
          </div>
        ))}
      </>
    );
  }

  const { votes, winner, was_tiebreak } = voteResult;

  return (
    <>
      {was_tiebreak && (
        <div className="split-badge">⚡ SPLIT VOTE — TIEBREAK ACTIVE</div>
      )}

      {votes.map((vote) => {
        const agent = agentDetails[vote.agent] || { name: vote.agent, role: 'UNKNOWN', cls: '' };
        const isWinner = winner === vote.agent;
        const scorePct = Math.round((vote.priority_score || 0) * 100);

        return (
          <div key={vote.agent} className={`agent-card ${agent.cls} ${isWinner ? 'winner' : ''}`}>
            <div className="agent-head">
              <div>
                <div className={`agent-name ${agent.cls}`}>{agent.name}</div>
                <div className="agent-role">{agent.role}</div>
              </div>
              {isWinner && <div className={`agent-won ${agent.cls}`}>✓ WON</div>}
            </div>
            <div className="score-row">
              <div className="score-label">PRIORITY</div>
              <div className="score-bar">
                <div className={`score-fill ${agent.cls}`} style={{ width: `${scorePct}%` }}></div>
              </div>
              <div className={`score-val ${agent.cls}`}>{vote.priority_score?.toFixed(2) || '0.00'}</div>
            </div>
            <div className="agent-action">
              <span className="action-label">ACTION → </span>
              <span className="action-val">
                {vote.proposed_action ? vote.proposed_action.replace('_', ' ') : 'HOLD'}
                {vote.target_zone ? ` @ ${vote.target_zone}` : ''}
              </span>
            </div>
            <div className="agent-reasoning">
              {vote.reasoning}
            </div>
          </div>
        );
      })}
    </>
  );
}
