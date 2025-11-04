import { Sparkles, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { InvestorSnapshot as InvestorSnapshotType } from '../types';
import MetricCard from './Snapshot/MetricCard';
import InvestmentRating from './Snapshot/InvestmentRating';

interface InvestorSnapshotProps {
  snapshot: InvestorSnapshotType;
}

export default function InvestorSnapshot({ snapshot }: InvestorSnapshotProps) {
  // Format large numbers
  const formatMarketCap = (value: number | null) => {
    if (!value) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(2)}`;
  };

  // Determine trend based on price change
  const getTrend = () => {
    const change = snapshot.price_change_pct;
    if (change === null || change === undefined) return { label: 'Unknown', color: 'text-gray-400' };
    if (change > 20) return { label: 'Strong Uptrend', color: 'text-success-400' };
    if (change > 5) return { label: 'Uptrend', color: 'text-success-500' };
    if (change > -5) return { label: 'Sideways', color: 'text-gray-400' };
    if (change > -20) return { label: 'Downtrend', color: 'text-danger-500' };
    return { label: 'Strong Downtrend', color: 'text-danger-400' };
  };

  const trend = getTrend();

  return (
    <div className="bg-gray-900 border-2 border-gray-800 rounded-xl overflow-hidden">
      {/* Header with Ticker Badge */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Sparkles className="w-5 h-5 text-primary-500" />
            <h2 className="text-lg font-bold text-white">
              Investor Snapshot
            </h2>
          </div>
          <span className="px-4 py-1.5 bg-primary-600/30 border-2 border-primary-500 text-primary-300 rounded-lg text-base font-mono font-bold">
            {snapshot.ticker}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-5">
        {/* Investment Rating - Centered and Prominent */}
        <InvestmentRating
          rating={snapshot.investment_rating}
          explanation={snapshot.rating_explanation}
        />

        {/* Divider */}
        <div className="border-t border-gray-800"></div>

        {/* Compact Core Metrics */}
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <div className="flex items-baseline space-x-2">
              <span className="text-gray-400 text-sm">💰 Current Price:</span>
              <span className="text-2xl font-bold text-white">
                ${snapshot.current_price?.toFixed(2) || 'N/A'}
              </span>
              {snapshot.price_change_pct !== null && snapshot.price_change_pct !== undefined && (
                <span className={`text-lg font-semibold ${snapshot.price_change_pct >= 0 ? 'text-success-400' : 'text-danger-400'}`}>
                  ({snapshot.price_change_pct >= 0 ? '+' : ''}{snapshot.price_change_pct.toFixed(2)}%)
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className="text-gray-400">
              Market Cap: <span className="text-white font-semibold">{formatMarketCap(snapshot.market_cap)}</span>
              {' | '}
              P/E: <span className="text-white font-semibold">{snapshot.pe_ratio ? snapshot.pe_ratio.toFixed(1) : 'N/A'}</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-gray-400">📈 Trend:</span>
              <span className={`font-semibold ${trend.color}`}>{trend.label}</span>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-800"></div>

        {/* Key Highlights - Compact List */}
        {snapshot.key_highlights && snapshot.key_highlights.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-success-400 flex items-center space-x-2 mb-3">
              <CheckCircle2 className="w-4 h-4" />
              <span>Key Highlights</span>
            </h3>
            <ul className="space-y-2">
              {snapshot.key_highlights.map((highlight, index) => (
                <li key={index} className="flex items-start space-x-2 text-sm">
                  <span className="flex-shrink-0 text-success-400 font-bold mt-0.5">{index + 1}.</span>
                  <span className="text-gray-300">{highlight}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Risk Warnings - Compact List */}
        {snapshot.risk_warnings && snapshot.risk_warnings.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-danger-400 flex items-center space-x-2 mb-3">
              <AlertTriangle className="w-4 h-4" />
              <span>Risk Warnings</span>
            </h3>
            <ul className="space-y-2">
              {snapshot.risk_warnings.map((risk, index) => (
                <li key={index} className="flex items-start space-x-2 text-sm">
                  <span className="flex-shrink-0 text-danger-400 font-bold mt-0.5">{index + 1}.</span>
                  <span className="text-gray-300">{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Footer Tip */}
      <div className="bg-gray-800/50 px-6 py-3 border-t border-gray-700">
        <p className="text-xs text-gray-400">
          <span className="text-primary-400 font-medium">💡 Tip:</span>
          {' '}Switch to "Detailed" mode for comprehensive analysis and professional charts.
        </p>
      </div>
    </div>
  );
}
