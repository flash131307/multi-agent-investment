import { useState } from 'react';
import { QueryClient, QueryClientProvider, useMutation, useQueryClient } from '@tanstack/react-query';
import { researchApi } from './api/client';
import Header from './components/Header';
import QueryInput from './components/QueryInput';
import LoadingState from './components/LoadingState';
import ReportDisplay from './components/ReportDisplay';
import SessionSidebar from './components/SessionSidebar';
import SessionHistory from './components/SessionHistory';
import ErrorState from './components/ErrorState';
import EmptyState from './components/EmptyState';
import type { ResearchQueryResponse } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function AppContent() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'new' | 'history'>('new');
  const [currentReport, setCurrentReport] = useState<ResearchQueryResponse | null>(null);
  const queryClient = useQueryClient();

  const submitQueryMutation = useMutation({
    mutationFn: researchApi.submitQuery,
    onSuccess: (data) => {
      setCurrentReport(data);
      setCurrentSessionId(data.session_id);
      setViewMode('new');
      // Invalidate sessions to refresh the sidebar
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  const handleSubmitQuery = (query: string) => {
    submitQueryMutation.mutate({
      query,
      session_id: viewMode === 'new' ? undefined : currentSessionId || undefined,
    });
  };

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setViewMode('history');
    setCurrentReport(null);
  };

  const handleNewSession = () => {
    setCurrentSessionId(null);
    setViewMode('new');
    setCurrentReport(null);
    submitQueryMutation.reset();
  };

  const handleRetry = () => {
    submitQueryMutation.reset();
  };

  const handleRequestDeepAnalysis = async (ticker: string) => {
    try {
      await researchApi.requestDeepAnalysis(ticker);
      // Note: The component will show processing state
      // User needs to query again after ~60 seconds
    } catch (error) {
      console.error('Failed to request deep analysis:', error);
    }
  };

  const handleRefreshQuery = (ticker: string) => {
    // Re-submit query to get updated report with EDGAR data
    submitQueryMutation.mutate({
      query: `Should I invest in ${ticker}?`,
      session_id: currentSessionId || undefined
    });
  };

  return (
    <div className="flex flex-col h-screen bg-gray-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <SessionSidebar
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
        />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="max-w-5xl mx-auto p-6 space-y-6">
            {/* Query Input - Always visible */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <QueryInput
                onSubmit={handleSubmitQuery}
                isLoading={submitQueryMutation.isPending}
              />
            </div>

            {/* Content Area */}
            <div>
              {submitQueryMutation.isPending && <LoadingState />}

              {submitQueryMutation.isError && (
                <ErrorState
                  error={submitQueryMutation.error as Error}
                  onRetry={handleRetry}
                />
              )}

              {submitQueryMutation.isSuccess && currentReport && viewMode === 'new' && (
                <ReportDisplay
                  report={currentReport}
                  onRequestDeepAnalysis={handleRequestDeepAnalysis}
                  onRefreshQuery={handleRefreshQuery}
                />
              )}

              {viewMode === 'history' && currentSessionId && (
                <SessionHistory sessionId={currentSessionId} />
              )}

              {!submitQueryMutation.isPending &&
                !submitQueryMutation.isError &&
                !currentReport &&
                viewMode === 'new' && (
                  <EmptyState />
                )}
            </div>
          </div>
        </main>
      </div>
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
