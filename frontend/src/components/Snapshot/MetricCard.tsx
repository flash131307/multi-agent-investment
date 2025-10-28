import { TrendingUp, TrendingDown } from 'lucide-react';
import FinancialTermTooltip from '../FinancialTermTooltip';

interface MetricCardProps {
  label: string;
  value: string | number | null;
  change?: number | null;
  term?: string;
  format?: 'currency' | 'percent' | 'number' | 'large-number';
}

export default function MetricCard({ label, value, change, term, format = 'number' }: MetricCardProps) {
  const formatValue = () => {
    if (value === null || value === undefined) return 'N/A';

    switch (format) {
      case 'currency':
        return `$${Number(value).toFixed(2)}`;
      case 'percent':
        return `${Number(value).toFixed(2)}%`;
      case 'large-number':
        // Format market cap in billions
        const num = Number(value);
        if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
        return `$${num.toFixed(2)}`;
      default:
        return value;
    }
  };

  const isPositiveChange = change !== null && change !== undefined && change >= 0;
  const hasChange = change !== null && change !== undefined;

  const CardContent = (
    <div className={`p-4 rounded-lg border transition-all ${
      hasChange
        ? isPositiveChange
          ? 'bg-success-950/20 border-success-800/50 hover:border-success-700'
          : 'bg-error-950/20 border-error-800/50 hover:border-error-700'
        : 'bg-gray-900 border-gray-800 hover:border-gray-700'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs text-gray-500 mb-1">{label}</p>
          <p className={`text-2xl font-bold ${
            hasChange
              ? isPositiveChange
                ? 'text-success-400'
                : 'text-error-400'
              : 'text-white'
          }`}>
            {formatValue()}
          </p>
        </div>
        {hasChange && (
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-full ${
            isPositiveChange
              ? 'bg-success-950/50 text-success-400'
              : 'bg-error-950/50 text-error-400'
          }`}>
            {isPositiveChange ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            <span className="text-xs font-semibold">
              {isPositiveChange ? '+' : ''}{change.toFixed(2)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );

  if (term) {
    return (
      <FinancialTermTooltip term={term} showIcon={false}>
        {CardContent}
      </FinancialTermTooltip>
    );
  }

  return CardContent;
}
