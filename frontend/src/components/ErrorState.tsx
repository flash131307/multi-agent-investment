import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  error: Error;
  onRetry?: () => void;
}

export default function ErrorState({ error, onRetry }: ErrorStateProps) {
  return (
    <div className="bg-danger-950/20 border border-danger-800/50 rounded-lg p-8">
      <div className="max-w-xl mx-auto text-center space-y-4">
        <div className="inline-flex p-4 bg-danger-600/10 rounded-full">
          <AlertCircle className="w-12 h-12 text-danger-500" />
        </div>

        <div className="space-y-2">
          <h3 className="text-xl font-semibold text-danger-400">
            Something went wrong
          </h3>
          <p className="text-gray-400">
            {error.message || 'An unexpected error occurred while processing your request.'}
          </p>
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center space-x-2 bg-danger-600 hover:bg-danger-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
          >
            <RefreshCw className="w-5 h-5" />
            <span>Try Again</span>
          </button>
        )}

        <div className="text-sm text-gray-500 pt-4 border-t border-gray-800">
          <p>If the problem persists, please check:</p>
          <ul className="mt-2 space-y-1 text-left max-w-md mx-auto">
            <li>• Backend API is running at http://localhost:8000</li>
            <li>• Your internet connection is stable</li>
            <li>• The query contains valid stock symbols or company names</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
