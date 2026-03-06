import { TrendingUp, TrendingDown, Minus, Shield, AlertTriangle } from 'lucide-react';
import type { AnalysisResponse, Direction, RiskMode } from '../types';
import AgentSignalCard from './AgentSignalCard';
import ConsistencyMeter from './ConsistencyMeter';

interface DecisionDisplayProps {
  result: AnalysisResponse;
}

function getDirectionConfig(direction: Direction) {
  switch (direction) {
    case 'BUY':
      return {
        icon: TrendingUp,
        label: 'BUY',
        color: 'text-success-400',
        bg: 'from-success-950/30 to-success-950/10',
        border: 'border-success-800/50',
        glow: 'shadow-success-900/20',
      };
    case 'SELL':
      return {
        icon: TrendingDown,
        label: 'SELL',
        color: 'text-danger-400',
        bg: 'from-danger-950/30 to-danger-950/10',
        border: 'border-danger-800/50',
        glow: 'shadow-danger-900/20',
      };
    case 'NEUTRAL':
      return {
        icon: Minus,
        label: 'NEUTRAL',
        color: 'text-gray-400',
        bg: 'from-gray-800/50 to-gray-900/50',
        border: 'border-gray-700',
        glow: '',
      };
  }
}

function getRiskIcon(riskMode: RiskMode) {
  switch (riskMode) {
    case 'NORMAL':
      return <Shield className="w-4 h-4 text-success-500" />;
    case 'CAUTIOUS':
      return <Shield className="w-4 h-4 text-yellow-500" />;
    case 'RISK':
      return <AlertTriangle className="w-4 h-4 text-danger-500" />;
  }
}

export default function DecisionDisplay({ result }: DecisionDisplayProps) {
  const { decision, agents, ticker, warnings } = result;
  const config = getDirectionConfig(decision.direction);
  const Icon = config.icon;

  return (
    <div className="space-y-6">
      {/* Recommendation Card */}
      <div className={`bg-gradient-to-br ${config.bg} border ${config.border} rounded-xl p-6 shadow-lg ${config.glow}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2 text-gray-400 text-sm">
            <span className="font-mono font-bold text-primary-400 text-base">{ticker}</span>
            <span>Analysis Result</span>
          </div>
          <div className="flex items-center space-x-1.5">
            {getRiskIcon(decision.risk_mode)}
            <span className="text-xs text-gray-400">{decision.risk_mode}</span>
          </div>
        </div>

        {/* Direction + Confidence */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-xl bg-gray-900/50 ${config.color}`}>
              <Icon className="w-10 h-10" />
            </div>
            <div>
              <h2 className={`text-3xl font-bold ${config.color}`}>{config.label}</h2>
              <p className="text-sm text-gray-500">Recommendation</p>
            </div>
          </div>
          <div className="flex-1" />
          <div className="text-right">
            <p className={`text-3xl font-mono font-bold ${config.color}`}>
              {Math.round(decision.confidence * 100)}%
            </p>
            <p className="text-sm text-gray-500">Confidence</p>
          </div>
        </div>

        {/* Aggregated score */}
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Aggregated Score</span>
            <span className="font-mono font-semibold text-gray-300">
              {decision.aggregated_score >= 0 ? '+' : ''}{decision.aggregated_score.toFixed(3)}
            </span>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="bg-yellow-950/20 border border-yellow-800/30 rounded-lg p-4 space-y-2">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            <span className="text-sm font-medium text-yellow-400">Warnings</span>
          </div>
          <ul className="space-y-1">
            {warnings.map((w, i) => (
              <li key={i} className="text-xs text-yellow-400/80 pl-6">
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Consistency Meter */}
      <ConsistencyMeter
        score={decision.consistency_score}
        riskMode={decision.risk_mode}
      />

      {/* Agent Signal Cards */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Agent Signals</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentSignalCard key={agent.agent_name} signal={agent} />
          ))}
        </div>
      </div>

      {/* Reasoning */}
      {decision.reasoning && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Decision Reasoning</h3>
          <p className="text-sm text-gray-400 leading-relaxed whitespace-pre-line">
            {decision.reasoning}
          </p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <p className="text-xs text-gray-500 text-center">
          This analysis is generated by AI agents and should not be considered financial advice.
          Always conduct your own research and consult a qualified financial advisor.
        </p>
      </div>
    </div>
  );
}
