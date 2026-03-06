import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (ticker: string) => void;
  isLoading: boolean;
}

const EXAMPLE_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'AMZN'];

export default function QueryInput({ onSubmit, isLoading }: QueryInputProps) {
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = ticker.trim().toUpperCase();
    if (cleaned && !isLoading) {
      onSubmit(cleaned);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex space-x-3">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter stock ticker (e.g., AAPL)"
            className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent font-mono text-lg tracking-wider transition-all"
            disabled={isLoading}
            maxLength={10}
          />
          <button
            type="submit"
            disabled={!ticker.trim() || isLoading}
            className="bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 disabled:from-gray-700 disabled:to-gray-800 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center space-x-2 shadow-lg shadow-primary-900/50 disabled:shadow-none"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
            <span>{isLoading ? 'Analyzing...' : 'Analyze'}</span>
          </button>
        </div>
      </form>

      {!isLoading && (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-gray-400 text-sm">
            <Sparkles className="w-4 h-4" />
            <span>Quick picks:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_TICKERS.map((t) => (
              <button
                key={t}
                onClick={() => { setTicker(t); onSubmit(t); }}
                className="px-3 py-1.5 bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-primary-700 rounded-lg text-sm font-mono font-semibold text-gray-300 hover:text-primary-400 transition-all duration-200"
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
