import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Clock, Plus, ChevronRight, Loader2 } from 'lucide-react';
import { researchApi } from '../api/client';
import type { SessionSummary } from '../types';

interface SessionSidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
}

export default function SessionSidebar({
  currentSessionId,
  onSessionSelect,
  onNewSession,
}: SessionSidebarProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['sessions'],
    queryFn: researchApi.getSessions,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const diffInMinutes = Math.floor(diffInHours * 60);
      return diffInMinutes <= 1 ? 'Just now' : `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const truncateQuery = (query: string | null | undefined, maxLength: number = 60) => {
    if (!query) return 'No query available';
    if (query.length <= maxLength) return query;
    return query.substring(0, maxLength) + '...';
  };

  return (
    <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <button
          onClick={onNewSession}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>New Research Query</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="p-4 space-y-2">
          <div className="flex items-center space-x-2 text-gray-400 text-sm mb-4">
            <MessageSquare className="w-4 h-4" />
            <span>Recent Sessions</span>
            {data && (
              <span className="ml-auto text-xs bg-gray-800 px-2 py-0.5 rounded-full">
                {data.total_count}
              </span>
            )}
          </div>

          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-gray-600 animate-spin" />
            </div>
          )}

          {error && (
            <div className="text-sm text-danger-400 bg-danger-950/20 border border-danger-800/50 rounded-lg p-4">
              Failed to load sessions. Please try again.
            </div>
          )}

          {data && data.sessions.length === 0 && (
            <div className="text-sm text-gray-500 text-center py-8">
              No sessions yet. Start a new research query above.
            </div>
          )}

          {data?.sessions.map((session) => (
            <SessionItem
              key={session.session_id}
              session={session}
              isActive={session.session_id === currentSessionId}
              onClick={() => onSessionSelect(session.session_id)}
              formatDate={formatDate}
              truncateQuery={truncateQuery}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface SessionItemProps {
  session: SessionSummary;
  isActive: boolean;
  onClick: () => void;
  formatDate: (date: string) => string;
  truncateQuery: (query: string | null | undefined, maxLength?: number) => string;
}

function SessionItem({ session, isActive, onClick, formatDate, truncateQuery }: SessionItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg transition-all duration-200 group ${
        isActive
          ? 'bg-primary-600/20 border border-primary-600/50'
          : 'bg-gray-800/50 hover:bg-gray-800 border border-gray-700/50 hover:border-gray-700'
      }`}
    >
      <div className="flex items-start justify-between space-x-2">
        <div className="flex-1 min-w-0 space-y-1">
          <p className={`text-sm font-medium line-clamp-2 ${
            isActive ? 'text-primary-300' : 'text-gray-300'
          }`}>
            {truncateQuery(session.first_query)}
          </p>
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>{formatDate(session.updated_at)}</span>
            <span className="text-gray-700">•</span>
            <span>{session.message_count} msg{session.message_count !== 1 ? 's' : ''}</span>
          </div>
        </div>
        <ChevronRight className={`w-4 h-4 flex-shrink-0 transition-transform ${
          isActive ? 'text-primary-500 transform translate-x-1' : 'text-gray-600 group-hover:text-gray-500'
        }`} />
      </div>
    </button>
  );
}
