import { HelpCircle } from 'lucide-react';
import { useState } from 'react';

interface FinancialTerm {
  term: string;
  definition: string;
  example?: string;
}

// Financial terms dictionary
const FINANCIAL_TERMS: Record<string, FinancialTerm> = {
  'P/E': {
    term: 'P/E Ratio (Price-to-Earnings)',
    definition: 'The price per share divided by earnings per share. It shows how much investors are willing to pay for each dollar of earnings.',
    example: 'A P/E of 20 means investors pay $20 for every $1 of annual earnings. Lower P/E may indicate undervaluation, but high-growth stocks often have high P/E ratios.'
  },
  'P/B': {
    term: 'P/B Ratio (Price-to-Book)',
    definition: 'The price per share divided by book value per share. It compares market value to the company\'s net asset value.',
    example: 'A P/B below 1.0 suggests the stock trades below its book value, which may indicate undervaluation or financial distress.'
  },
  'P/S': {
    term: 'P/S Ratio (Price-to-Sales)',
    definition: 'The price per share divided by revenue per share. Useful for valuing companies that aren\'t yet profitable.',
    example: 'A P/S of 2 means investors pay $2 for every $1 of annual sales. Growth companies often have higher P/S ratios.'
  },
  'RSI': {
    term: 'RSI (Relative Strength Index)',
    definition: 'A momentum indicator measuring the speed and magnitude of price changes. Ranges from 0 to 100.',
    example: 'RSI above 70 suggests overbought (potentially overvalued), below 30 suggests oversold (potentially undervalued).'
  },
  'MACD': {
    term: 'MACD (Moving Average Convergence Divergence)',
    definition: 'A trend-following indicator showing the relationship between two moving averages of a stock\'s price.',
    example: 'When MACD crosses above the signal line, it may indicate a bullish trend. Below suggests bearish.'
  },
  'Volume': {
    term: 'Trading Volume',
    definition: 'The number of shares traded during a given period. High volume indicates strong investor interest.',
    example: 'Sudden volume spikes often accompany significant news or price movements.'
  },
  '52-Week High': {
    term: '52-Week High',
    definition: 'The highest price at which a stock traded during the past year.',
    example: 'If a stock is near its 52-week high, it may be in a strong uptrend, but could also be overbought.'
  },
  '52-Week Low': {
    term: '52-Week Low',
    definition: 'The lowest price at which a stock traded during the past year.',
    example: 'Stocks near 52-week lows may be undervalued or facing fundamental challenges.'
  },
  'Market Cap': {
    term: 'Market Capitalization',
    definition: 'The total market value of a company\'s outstanding shares (share price × number of shares).',
    example: 'Large-cap (>$10B), Mid-cap ($2-10B), Small-cap (<$2B). Larger caps are typically less volatile.'
  },
  'Dividend Yield': {
    term: 'Dividend Yield',
    definition: 'Annual dividends per share divided by current stock price, expressed as a percentage.',
    example: 'A 3% yield means you earn $3 per year for every $100 invested, plus any capital gains.'
  },
  'EPS': {
    term: 'EPS (Earnings Per Share)',
    definition: 'Company\'s profit divided by the outstanding shares. A key measure of profitability.',
    example: 'Growing EPS over time typically indicates improving business performance.'
  },
  'Beta': {
    term: 'Beta',
    definition: 'Measures a stock\'s volatility relative to the overall market. Market beta = 1.0.',
    example: 'Beta > 1 means more volatile than market. Beta < 1 means less volatile. Negative beta moves opposite to market.'
  },
  'Sentiment': {
    term: 'Market Sentiment',
    definition: 'The overall attitude of investors toward a stock or market, often measured through news and social media.',
    example: 'Positive sentiment (bullish) suggests optimism. Negative sentiment (bearish) suggests pessimism. Neutral is mixed.'
  },
  'Analyst Consensus': {
    term: 'Analyst Consensus',
    definition: 'The average recommendation from financial analysts (Strong Buy, Buy, Hold, Sell, Strong Sell).',
    example: 'If most analysts recommend "Buy", they believe the stock will outperform the market.'
  }
};

interface FinancialTermTooltipProps {
  term: keyof typeof FINANCIAL_TERMS | string;
  children?: React.ReactNode;
  showIcon?: boolean;
  className?: string;
}

export default function FinancialTermTooltip({
  term,
  children,
  showIcon = true,
  className = ''
}: FinancialTermTooltipProps) {
  const [isHovered, setIsHovered] = useState(false);

  const termInfo = FINANCIAL_TERMS[term];

  // If term not found, just render children
  if (!termInfo) {
    return <>{children}</>;
  }

  return (
    <div className="relative inline-block">
      <div
        className={`inline-flex items-center space-x-1 cursor-help ${className}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {children}
        {showIcon && (
          <HelpCircle className="w-3.5 h-3.5 text-gray-500 hover:text-primary-400 transition-colors" />
        )}
      </div>

      {/* Tooltip */}
      {isHovered && (
        <div className="absolute z-50 w-80 p-4 bg-gray-800 border border-gray-700 rounded-lg shadow-2xl bottom-full left-1/2 transform -translate-x-1/2 mb-2 pointer-events-none">
          {/* Arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-px">
            <div className="border-8 border-transparent border-t-gray-700"></div>
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-primary-400">{termInfo.term}</h4>
            <p className="text-xs text-gray-300 leading-relaxed">{termInfo.definition}</p>
            {termInfo.example && (
              <div className="pt-2 border-t border-gray-700">
                <p className="text-xs text-gray-400 italic">
                  <span className="font-medium text-gray-300">Example:</span> {termInfo.example}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Export term keys for easy access
export const TERM_KEYS = Object.keys(FINANCIAL_TERMS) as Array<keyof typeof FINANCIAL_TERMS>;

// Helper component for inline term highlighting
interface InlineTermProps {
  term: keyof typeof FINANCIAL_TERMS | string;
  children: React.ReactNode;
}

export function InlineTerm({ term, children }: InlineTermProps) {
  return (
    <FinancialTermTooltip term={term} showIcon={false}>
      <span className="underline decoration-dotted decoration-gray-600 hover:decoration-primary-500 hover:text-primary-400 transition-all cursor-help">
        {children}
      </span>
    </FinancialTermTooltip>
  );
}
