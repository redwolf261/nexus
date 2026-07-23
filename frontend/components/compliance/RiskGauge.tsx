import React from 'react';

interface RiskGaugeProps {
  score: number;       // 0 to 100
  riskBand: string;    // LOW, MODERATE, HIGH, CRITICAL
  complianceScore?: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ score, riskBand, complianceScore }) => {
  const compScore = complianceScore ?? Math.max(0, 100 - score);

  const getBandColor = (band: string) => {
    switch (band.toUpperCase()) {
      case 'CRITICAL':
        return { text: 'text-rose-400', bg: 'bg-rose-950', border: 'border-rose-700', fill: '#f43f5e' };
      case 'HIGH':
        return { text: 'text-amber-400', bg: 'bg-amber-950', border: 'border-amber-700', fill: '#fbbf24' };
      case 'MODERATE':
        return { text: 'text-yellow-300', bg: 'bg-yellow-950', border: 'border-yellow-700', fill: '#fde047' };
      default:
        return { text: 'text-emerald-400', bg: 'bg-emerald-950', border: 'border-emerald-700', fill: '#34d399' };
    }
  };

  const style = getBandColor(riskBand);

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-slate-200 flex flex-col items-center justify-center space-y-3">
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
        Operational Compliance Score
      </div>

      <div className="relative flex items-center justify-center w-36 h-36">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          <path
            className="text-slate-800"
            strokeWidth="3.5"
            stroke="currentColor"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            strokeDasharray={`${compScore}, 100`}
            strokeWidth="3.5"
            stroke={style.fill}
            strokeLinecap="round"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold text-slate-100">{compScore.toFixed(0)}%</span>
          <span className="text-[10px] text-slate-400">COMPLIANT</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">Risk Score:</span>
        <span className="font-bold text-slate-200">{score.toFixed(1)}/100</span>
        <span className={`px-2 py-0.5 rounded text-xs font-bold border ${style.bg} ${style.text} ${style.border}`}>
          {riskBand}
        </span>
      </div>
    </div>
  );
};
