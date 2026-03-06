import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import type { AgentSignalResponse, Direction, Strength } from '../types';

interface AgentSignalCardProps {
  signal: AgentSignalResponse;
}

const AGENT_LABELS: Record<string, string> = {
  technical: 'Technical Analysis',
  sentiment: 'News Sentiment',
  fundamental: 'Fundamental Analysis',
};

const AGENT_DESCRIPTIONS: Record<string, string> = {
  technical: 'ReAct pattern with 6 indicator tools',
  sentiment: 'FinBERT three-layer funnel',
  fundamental: 'Plan-and-Solve with RAG',
};

function getDirectionStyle(direction: Direction) {
  switch (direction) {
    case 'BUY':
      return {
        icon: TrendingUp,
        color: 'text-success-400',
        bg: 'bg-success-950/20 border-success-800/50',
        badge: 'bg-success-600',
      };
    case 'SELL':
      return {
        icon: TrendingDown,
        color: 'text-danger-400',
        bg: 'bg-danger-950/20 border-danger-800/50',
        badge: 'bg-danger-600',
      };
    case 'NEUTRAL':
      return {
        icon: Minus,
        color: 'text-gray-400',
        bg: 'bg-gray-800/50 border-gray-700',
        badge: 'bg-gray-600',
      };
  }
}

function getStrengthLabel(strength: Strength): string {
  return strength.charAt(0) + strength.slice(1).toLowerCase();
}

export default function AgentSignalCard({ signal }: AgentSignalCardProps) {
  const label = AGENT_LABELS[signal.agent_name] ?? signal.agent_name;
  const description = AGENT_DESCRIPTIONS[signal.agent_name] ?? '';

  // Error / failed state
  if (signal.error || signal.direction === null) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-3 opacity-60">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-gray-400">{label}</h4>
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
        </div>
        <p className="text-xs text-gray-500">{description}</p>
        <div className="text-xs text-yellow-400/80 bg-yellow-950/20 border border-yellow-800/30 rounded px-2 py-1.5">
          {signal.error ?? 'Agent did not return a signal (timeout or failure)'}
        </div>
      </div>
    );
  }

  const style = getDirectionStyle(signal.direction);
  const Icon = style.icon;

  return (
    <div className={`border rounded-lg p-4 space-y-3 ${style.bg}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-200">{label}</h4>
        <span className={`text-xs font-bold px-2 py-0.5 rounded text-white ${style.badge}`}>
          {signal.direction}
        </span>
      </div>

      {/* Metrics row */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1.5">
          <Icon className={`w-5 h-5 ${style.color}`} />
          <span className={`text-sm font-semibold ${style.color}`}>
            {getStrengthLabel(signal.strength!)}
          </span>
        </div>
        <div className="flex-1" />
        <div className="text-right">
          <span className="text-xs text-gray-500">Confidence</span>
          <p className="text-sm font-mono font-bold text-gray-200">
            {Math.round(signal.confidence! * 100)}%
          </p>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${style.badge}`}
          style={{ width: `${signal.confidence! * 100}%` }}
        />
      </div>

      {/* Reasoning */}
      {signal.reasoning && (
        <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">
          {signal.reasoning}
        </p>
      )}

      {/* Description */}
      <p className="text-xs text-gray-600">{description}</p>
    </div>
  );
}
