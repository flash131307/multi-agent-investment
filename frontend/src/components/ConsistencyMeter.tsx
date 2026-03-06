import { Activity } from 'lucide-react';
import type { RiskMode } from '../types';

interface ConsistencyMeterProps {
  score: number;
  riskMode: RiskMode;
}

function getRiskColor(riskMode: RiskMode) {
  switch (riskMode) {
    case 'NORMAL':
      return { bar: 'bg-success-500', text: 'text-success-400', label: 'Normal' };
    case 'CAUTIOUS':
      return { bar: 'bg-yellow-500', text: 'text-yellow-400', label: 'Cautious' };
    case 'RISK':
      return { bar: 'bg-danger-500', text: 'text-danger-400', label: 'High Risk' };
  }
}

export default function ConsistencyMeter({ score, riskMode }: ConsistencyMeterProps) {
  const colors = getRiskColor(riskMode);
  const percentage = Math.round(score * 100);

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-300">Agent Consistency</span>
        </div>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${colors.text} bg-gray-900`}>
          {colors.label}
        </span>
      </div>

      {/* Progress bar */}
      <div className="relative">
        <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${colors.bar}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {/* Threshold markers */}
        <div className="absolute top-0 left-[40%] w-px h-2 bg-gray-500" title="Cautious threshold (0.4)" />
        <div className="absolute top-0 left-[70%] w-px h-2 bg-gray-500" title="Normal threshold (0.7)" />
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Conflicting</span>
        <span className={`font-mono font-bold ${colors.text}`}>{percentage}%</span>
        <span>Aligned</span>
      </div>
    </div>
  );
}
