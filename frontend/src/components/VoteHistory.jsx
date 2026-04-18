import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function VoteHistory({ history }) {
  const chartData = useMemo(() => {
    if (!history || history.length === 0) {
      return [
        { tick: -5, CASPER: 0.8, MELCHIOR: 0.6, BALTHASAR: 0.5 },
        { tick: -4, CASPER: 0.82, MELCHIOR: 0.65, BALTHASAR: 0.4 },
        { tick: -3, CASPER: 0.91, MELCHIOR: 0.6, BALTHASAR: 0.7 },
        { tick: -2, CASPER: 0.85, MELCHIOR: 0.7, BALTHASAR: 0.87 },
        { tick: -1, CASPER: 0.9, MELCHIOR: 0.62, BALTHASAR: 0.85 }
      ];
    }
    return history.map(h => {
      const dataPoint = { tick: h.tick };
      h.votes?.forEach(v => {
        dataPoint[v.agent] = v.priority_score;
      });
      return dataPoint;
    });
  }, [history]);

  return (
    <div className="h-[220px] shrink-0 flex flex-col border-t border-navyBorder mt-auto bg-[rgba(13,27,42,0.8)] shadow-inner">
      <div className="font-mono-custom text-[9px] tracking-[3px] text-muted px-4 py-2 border-b border-navyBorder shrink-0 flex items-center justify-between">
        <span>PRIORITY SCORE HISTORY</span>
        <span className="text-teal tracking-[1px] animate-pulse">LIVE FEED //</span>
      </div>
      <div className="flex-1 p-2 relative flex flex-col justify-end min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 15, right: 15, left: -20, bottom: 5 }}>
            <defs>
              <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
              <filter id="glow-amber" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
              <filter id="glow-teal" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>
            <XAxis dataKey="tick" stroke="#1A3045" tick={{ fill: '#4A7090', fontSize: 9, fontFamily: 'Share Tech Mono' }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 1]} stroke="#1A3045" tick={{ fill: '#4A7090', fontSize: 9, fontFamily: 'Share Tech Mono' }} axisLine={false} tickLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(15,32,48,0.9)', border: '1px solid #1A3045', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}
              itemStyle={{ fontSize: 10, fontFamily: 'Share Tech Mono', fontWeight: 'bold' }}
              labelStyle={{ color: '#4A7090', fontSize: 10, fontFamily: 'Share Tech Mono' }}
            />
            <Line type="monotone" dataKey="CASPER" stroke="#FF3D5A" strokeWidth={2.5} dot={false} isAnimationActive={true} filter="url(#glow-red)" />
            <Line type="monotone" dataKey="MELCHIOR" stroke="#FFB020" strokeWidth={2.5} dot={false} isAnimationActive={true} filter="url(#glow-amber)" />
            <Line type="monotone" dataKey="BALTHASAR" stroke="#00D4B8" strokeWidth={2.5} dot={false} isAnimationActive={true} filter="url(#glow-teal)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
