import { TrendingUp, TrendingDown, Minus, AlertTriangle, Target } from 'lucide-react';

interface InvestmentRatingProps {
  rating: 'strong_buy' | 'buy' | 'hold' | 'sell' | 'strong_sell';
  explanation: string;
}

export default function InvestmentRating({ rating, explanation }: InvestmentRatingProps) {
  const getRatingConfig = () => {
    switch (rating) {
      case 'strong_buy':
        return {
          label: 'STRONG BUY',
          emoji: '🟢',
          icon: TrendingUp,
          textColor: 'text-success-400',
        };
      case 'buy':
        return {
          label: 'BUY',
          emoji: '🟢',
          icon: TrendingUp,
          textColor: 'text-success-500',
        };
      case 'hold':
        return {
          label: 'HOLD',
          emoji: '🟡',
          icon: Minus,
          textColor: 'text-yellow-400',
        };
      case 'sell':
        return {
          label: 'SELL',
          emoji: '🔴',
          icon: TrendingDown,
          textColor: 'text-warning-500',
        };
      case 'strong_sell':
        return {
          label: 'STRONG SELL',
          emoji: '🔴',
          icon: AlertTriangle,
          textColor: 'text-error-400',
        };
    }
  };

  const config = getRatingConfig();
  const Icon = config.icon;

  return (
    <div className="text-center space-y-3">
      {/* Rating Badge */}
      <div className="flex items-center justify-center space-x-3">
        <span className="text-3xl">{config.emoji}</span>
        <h3 className={`text-2xl font-bold ${config.textColor}`}>
          {config.label}
        </h3>
        <Icon className={`w-6 h-6 ${config.textColor}`} />
      </div>

      {/* Explanation */}
      <p className="text-gray-300 text-sm leading-relaxed max-w-2xl mx-auto">
        {explanation}
      </p>
    </div>
  );
}
