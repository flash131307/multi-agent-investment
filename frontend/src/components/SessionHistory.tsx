import { useQuery } from '@tanstack/react-query';
import { User, Bot, Loader2, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { researchApi } from '../api/client';

interface SessionHistoryProps {
  sessionId: string;
}

export default function SessionHistory({ sessionId }: SessionHistoryProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['session-history', sessionId],
    queryFn: () => researchApi.getSessionHistory(sessionId),
    enabled: !!sessionId,
  });

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-3">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin mx-auto" />
          <p className="text-gray-400">Loading session history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-950/20 border border-danger-800/50 rounded-lg p-6">
        <div className="flex items-center space-x-3 text-danger-400">
          <AlertCircle className="w-6 h-6 flex-shrink-0" />
          <div>
            <p className="font-semibold">Failed to load session history</p>
            <p className="text-sm text-danger-300 mt-1">Please try selecting the session again.</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data || data.messages.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
        <p className="text-gray-400">No messages in this session.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-gray-400 text-sm">
            <span className="font-medium text-gray-300">Session History</span>
            <span className="text-gray-700">•</span>
            <span>{data.message_count} message{data.message_count !== 1 ? 's' : ''}</span>
          </div>
          <div className="text-xs text-gray-500 font-mono">
            {sessionId.slice(0, 16)}...
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {data.messages.map((message, index) => (
          <div
            key={index}
            className={`flex items-start space-x-4 ${
              message.role === 'user' ? 'flex-row' : 'flex-row'
            }`}
          >
            {/* Avatar */}
            <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
              message.role === 'user'
                ? 'bg-gradient-to-br from-primary-600 to-primary-700'
                : 'bg-gradient-to-br from-gray-700 to-gray-800'
            }`}>
              {message.role === 'user' ? (
                <User className="w-5 h-5 text-white" />
              ) : (
                <Bot className="w-5 h-5 text-white" />
              )}
            </div>

            {/* Message Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                <span className={`text-sm font-semibold ${
                  message.role === 'user' ? 'text-primary-400' : 'text-gray-300'
                }`}>
                  {message.role === 'user' ? 'You' : 'Research Assistant'}
                </span>
                <span className="text-xs text-gray-600">
                  {formatTime(message.timestamp)}
                </span>
              </div>
              <div className={`rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-gray-900 border border-gray-800'
                  : 'bg-gray-900 border border-gray-800'
              }`}>
                {message.role === 'user' ? (
                  <p className="text-gray-300 whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div className="markdown-content text-sm">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
