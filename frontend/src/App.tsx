import { useState } from 'react';
import { QueryClient, QueryClientProvider, useMutation } from '@tanstack/react-query';
import { submitAnalysis } from './api/client';
import Header from './components/Header';
import QueryInput from './components/QueryInput';
import LoadingState from './components/LoadingState';
import DecisionDisplay from './components/DecisionDisplay';
import ErrorState from './components/ErrorState';
import EmptyState from './components/EmptyState';
import type { AnalysisResponse } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function AppContent() {
  const [currentResult, setCurrentResult] = useState<AnalysisResponse | null>(null);

  const analyzeMutation = useMutation({
    mutationFn: submitAnalysis,
    onSuccess: (data) => {
      setCurrentResult(data);
    },
  });

  const handleAnalyze = (ticker: string) => {
    analyzeMutation.mutate({ ticker });
  };

  const handleRetry = () => {
    analyzeMutation.reset();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-950">
      <Header />

      <main className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="max-w-5xl mx-auto p-6 space-y-6">
          {/* Ticker Input */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <QueryInput
              onSubmit={handleAnalyze}
              isLoading={analyzeMutation.isPending}
            />
          </div>

          {/* Content Area */}
          {analyzeMutation.isPending && <LoadingState />}

          {analyzeMutation.isError && (
            <ErrorState
              error={analyzeMutation.error as Error}
              onRetry={handleRetry}
            />
          )}

          {analyzeMutation.isSuccess && currentResult && (
            <DecisionDisplay result={currentResult} />
          )}

          {!analyzeMutation.isPending &&
            !analyzeMutation.isError &&
            !currentResult && (
              <EmptyState />
            )}
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
