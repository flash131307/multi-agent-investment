import { FileStack, Clock, TrendingUp } from 'lucide-react';
import { useState } from 'react';

interface DeepAnalysisPromptProps {
  ticker: string;
  onRequestAnalysis: (ticker: string) => void;
}

export default function DeepAnalysisPrompt({ ticker, onRequestAnalysis }: DeepAnalysisPromptProps) {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleRequest = async () => {
    setIsProcessing(true);
    await onRequestAnalysis(ticker);
  };

  if (isProcessing) {
    return (
      <div className="bg-gradient-to-r from-blue-900/30 to-indigo-900/30 border border-blue-700/50 rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 rounded-full bg-blue-600/20 flex items-center justify-center animate-pulse">
              <FileStack className="w-6 h-6 text-blue-400" />
            </div>
          </div>

          <div className="flex-1 space-y-3">
            <div className="flex items-center space-x-3">
              <h3 className="text-lg font-semibold text-white">
                Downloading SEC 10-K Filing
              </h3>
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>

            <p className="text-gray-300">
              Processing {ticker}'s latest SEC filing for comprehensive financial analysis...
            </p>

            <div className="flex items-center space-x-2 text-sm text-blue-400">
              <Clock className="w-4 h-4" />
              <span>Estimated time: 30-60 seconds</span>
            </div>

            <div className="mt-4 bg-gray-800/50 rounded-lg p-4 space-y-2">
              <p className="text-sm text-gray-400">
                What we're analyzing:
              </p>
              <ul className="text-sm text-gray-300 space-y-1 ml-4">
                <li className="flex items-center space-x-2">
                  <span className="text-blue-400">•</span>
                  <span>Business operations and revenue streams</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-blue-400">•</span>
                  <span>Risk factors and management discussion</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-blue-400">•</span>
                  <span>Financial statements and detailed metrics</span>
                </li>
              </ul>
            </div>

            <p className="text-sm text-yellow-400/80 mt-4">
              Query {ticker} again in about a minute to see deep insights from the SEC filing.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-primary-900/20 to-indigo-900/20 border border-primary-700/50 rounded-lg p-6">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-primary-600/20 flex items-center justify-center">
            <FileStack className="w-6 h-6 text-primary-400" />
          </div>
        </div>

        <div className="flex-1 space-y-3">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <span>Want Deeper Insights?</span>
            <TrendingUp className="w-5 h-5 text-primary-400" />
          </h3>

          <p className="text-gray-300">
            This analysis uses real-time market data. For comprehensive insights including detailed
            financials, risk factors, and management discussion from SEC 10-K filings, enable deep analysis.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 py-3">
            <div className="bg-gray-800/50 rounded-lg p-3 space-y-1">
              <p className="text-sm font-semibold text-primary-400">Business Details</p>
              <p className="text-xs text-gray-400">Operations, revenue sources, competitive advantages</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 space-y-1">
              <p className="text-sm font-semibold text-primary-400">Risk Analysis</p>
              <p className="text-xs text-gray-400">Management discussion on risks and uncertainties</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 space-y-1">
              <p className="text-sm font-semibold text-primary-400">Financial Deep Dive</p>
              <p className="text-xs text-gray-400">Statement analysis and detailed metrics</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 pt-2">
            <button
              onClick={handleRequest}
              className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors flex items-center space-x-2 shadow-lg shadow-primary-900/50"
            >
              <FileStack className="w-4 h-4" />
              <span>Generate Deep Analysis</span>
            </button>

            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <Clock className="w-4 h-4" />
              <span>~60 seconds (one-time download)</span>
            </div>
          </div>

          <p className="text-xs text-gray-500">
            Deep analysis downloads and processes SEC 10-K filing. Results are cached for future queries.
          </p>
        </div>
      </div>
    </div>
  );
}
