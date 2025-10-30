import { FileStack, Clock, Sparkles, X, CheckCircle } from 'lucide-react';
import { useState, useEffect } from 'react';
import { researchApi } from '../api/client';

interface DeepAnalysisBannerProps {
  ticker: string;
  onRequestAnalysis: (ticker: string) => Promise<void>;
  onRefreshQuery?: (ticker: string) => void;
}

type BannerStatus = 'idle' | 'processing' | 'completed';

export default function DeepAnalysisBanner({ ticker, onRequestAnalysis, onRefreshQuery }: DeepAnalysisBannerProps) {
  const [status, setStatus] = useState<BannerStatus>('idle');
  const [countdown, setCountdown] = useState(60);
  const [isDismissed, setIsDismissed] = useState(false);

  // Countdown timer
  useEffect(() => {
    if (status === 'processing' && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (status === 'processing' && countdown === 0) {
      // Countdown finished, move to completed state
      setStatus('completed');

      // Auto-refresh query after 2 seconds
      setTimeout(() => {
        if (onRefreshQuery) {
          onRefreshQuery(ticker);
        }
      }, 2000);
    }
  }, [status, countdown, ticker, onRefreshQuery]);

  // Polling for completion (check every 5 seconds)
  useEffect(() => {
    if (status !== 'processing') {
      return; // Only poll when processing
    }

    const pollInterval = setInterval(async () => {
      try {
        const result = await researchApi.checkDeepAnalysisStatus(ticker);

        if (result.available) {
          // Data is ready! Immediately complete
          setStatus('completed');

          // Auto-refresh query after 1 second
          setTimeout(() => {
            if (onRefreshQuery) {
              onRefreshQuery(ticker);
            }
          }, 1000);
        }
      } catch (error) {
        console.error('Error checking deep analysis status:', error);
        // Continue polling on error
      }
    }, 5000); // Poll every 5 seconds

    // Cleanup on unmount or status change
    return () => clearInterval(pollInterval);
  }, [status, ticker, onRefreshQuery]);

  const handleRequest = async () => {
    setStatus('processing');
    setCountdown(60);
    try {
      await onRequestAnalysis(ticker);
    } catch (error) {
      console.error('Failed to request deep analysis:', error);
      // Reset on error
      setStatus('idle');
      setCountdown(60);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
  };

  if (isDismissed) {
    return null;
  }

  // Status: Completed
  if (status === 'completed') {
    return (
      <div className="bg-gradient-to-r from-green-900/40 to-emerald-900/40 border border-green-700/60 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 rounded-full bg-green-600/30 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
            </div>

            <div className="flex-1">
              <h3 className="text-base font-semibold text-white mb-1">
                ✅ Deep Analysis Ready!
              </h3>
              <p className="text-sm text-gray-300">
                Refreshing report with comprehensive SEC 10-K insights...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Status: Processing
  if (status === 'processing') {
    return (
      <div className="bg-gradient-to-r from-blue-900/40 to-indigo-900/40 border border-blue-700/60 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 rounded-full bg-blue-600/30 flex items-center justify-center animate-pulse">
                <FileStack className="w-5 h-5 text-blue-400" />
              </div>
            </div>

            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="text-base font-semibold text-white">
                  Processing {ticker} Deep Analysis
                </h3>
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
              <p className="text-sm text-gray-300">
                Downloading and analyzing SEC 10-K filing. Report will auto-refresh when ready.
              </p>
            </div>

            <div className="flex items-center space-x-2 text-sm font-medium text-blue-400 flex-shrink-0">
              <Clock className="w-4 h-4" />
              <span className="tabular-nums">{countdown}s</span>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-3 w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-blue-500 h-full transition-all duration-1000 ease-linear"
            style={{ width: `${((60 - countdown) / 60) * 100}%` }}
          />
        </div>
      </div>
    );
  }

  // Status: Idle (default)
  return (
    <div className="bg-gradient-to-r from-primary-900/30 to-indigo-900/30 border border-primary-700/60 rounded-lg p-4 mb-6 relative">
      <button
        onClick={handleDismiss}
        className="absolute top-3 right-3 text-gray-400 hover:text-gray-300 transition-colors"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="flex items-center justify-between pr-8">
        <div className="flex items-center space-x-3 flex-1">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 rounded-full bg-primary-600/30 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-400" />
            </div>
          </div>

          <div className="flex-1">
            <h3 className="text-base font-semibold text-white mb-1">
              Deep Analysis Available for {ticker}
            </h3>
            <p className="text-sm text-gray-300">
              Get comprehensive insights from SEC 10-K filing: business details, risk factors, and financial deep dive
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 flex-shrink-0 ml-4">
          <div className="hidden md:flex items-center space-x-2 text-sm text-gray-400">
            <Clock className="w-4 h-4" />
            <span>~60s</span>
          </div>

          <button
            onClick={handleRequest}
            className="px-5 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors flex items-center space-x-2 shadow-lg shadow-primary-900/50 whitespace-nowrap"
          >
            <FileStack className="w-4 h-4" />
            <span>Generate</span>
          </button>
        </div>
      </div>
    </div>
  );
}
