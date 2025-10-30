import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Calendar, TrendingUp, Database, FileText, BarChart3, CheckCircle2, XCircle, Sparkles, FileStack, Target, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import type { ResearchQueryResponse } from '../types';
import PriceChart from './Charts/PriceChart';
import PeerComparisonChart from './Charts/PeerComparisonChart';
import InvestorSnapshot from './InvestorSnapshot';
import DeepAnalysisBanner from './DeepAnalysisBanner';

interface ReportDisplayProps {
  report: ResearchQueryResponse;
  onRequestDeepAnalysis?: (ticker: string) => Promise<void>;
  onRefreshQuery?: (ticker: string) => void;
}

export default function ReportDisplay({ report, onRequestDeepAnalysis, onRefreshQuery }: ReportDisplayProps) {
  const [viewMode, setViewMode] = useState<'simple' | 'detailed'>('simple');

  const handleDeepAnalysisRequest = async (ticker: string) => {
    if (onRequestDeepAnalysis) {
      await onRequestDeepAnalysis(ticker);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Query Header */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <div className="flex items-center space-x-2 text-gray-400 text-sm mb-2">
              <FileText className="w-4 h-4" />
              <span>Research Query</span>
            </div>
            <h2 className="text-xl font-semibold text-white">{report.query}</h2>
          </div>

          {/* Tickers */}
          {report.tickers && report.tickers.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {report.tickers.map((ticker) => (
                <span
                  key={ticker}
                  className="px-3 py-1 bg-primary-600/20 border border-primary-600/50 text-primary-400 rounded-full text-sm font-mono font-semibold"
                >
                  {ticker}
                </span>
              ))}
            </div>
          )}

          {/* Metadata */}
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(report.timestamp)}</span>
            <span className="text-gray-700">•</span>
            <span className="font-mono">{report.session_id.slice(0, 8)}</span>
          </div>
        </div>
      </div>

      {/* Deep Analysis Banner - Top Placement */}
      {report.can_request_deep_analysis && report.tickers && report.tickers.length > 0 && (
        <DeepAnalysisBanner
          ticker={report.tickers[0]}
          onRequestAnalysis={handleDeepAnalysisRequest}
          onRefreshQuery={onRefreshQuery}
        />
      )}

      {/* View Mode Toggle */}
      <div className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-primary-500" />
          <span className="text-sm text-gray-300">
            View Mode
          </span>
        </div>
        <div className="flex items-center space-x-2 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('simple')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              viewMode === 'simple'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Simple</span>
          </button>
          <button
            onClick={() => setViewMode('detailed')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              viewMode === 'detailed'
                ? 'bg-primary-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            <FileStack className="w-4 h-4" />
            <span>Detailed</span>
          </button>
        </div>
      </div>

      {/* Data Availability Indicators with Error Details */}
      {viewMode === 'detailed' && (
        <div className="space-y-4">
          {/* Routing Decision Summary */}
          {report.intent && report.routing_flags && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Target className="w-4 h-4 text-primary-500" />
                <h3 className="text-sm font-medium text-gray-300">
                  Routing Decision
                </h3>
              </div>

              {/* Explanation text */}
              <p className="text-xs text-gray-500 mb-3 leading-relaxed">
                Router analyzed the query and determined which agents to activate.
                Check the indicators below for actual execution results.
              </p>

              {/* Intent */}
              <div>
                <p className="text-xs text-gray-500 mb-1">Detected Intent</p>
                <div className="flex items-center space-x-2">
                  <span className="px-3 py-1.5 bg-primary-950/30 border border-primary-800/50 text-primary-400 rounded-md text-sm font-medium">
                    {report.intent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <DataIndicator
              icon={TrendingUp}
              label="Market Data"
              agentName="market_data"
              available={report.market_data_available}
              error={report.agent_errors?.market_data}
              executed={report.executed_agents?.includes('market_data')}
            />
            <DataIndicator
              icon={FileText}
              label="Sentiment"
              agentName="sentiment"
              available={report.sentiment_available}
              error={report.agent_errors?.sentiment}
              executed={report.executed_agents?.includes('sentiment')}
            />
            <DataIndicator
              icon={BarChart3}
              label="Analyst Consensus"
              agentName="forward_looking"
              available={report.analyst_consensus_available}
              error={report.agent_errors?.forward_looking}
              executed={report.executed_agents?.includes('forward_looking')}
            />
            <DataIndicator
              icon={Database}
              label={`Context Retrieved (${report.context_retrieved})`}
              agentName="rag_retrieval"
              available={report.context_retrieved > 0}
              error={report.agent_errors?.rag_retrieval}
              executed={report.executed_agents?.includes('rag_retrieval')}
            />
          </div>
        </div>
      )}

      {/* Content - Switch between Simple (Snapshot) and Detailed (Full Report) */}
      {viewMode === 'simple' && report.snapshot ? (
        <>
          {/* Simple Mode: Investor Snapshot */}
          <InvestorSnapshot snapshot={report.snapshot} />

          {/* Simple Mode: Simplified Chart (Price only) */}
          {report.visualization_data && report.visualization_data.length > 0 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white flex items-center space-x-2">
                  <BarChart3 className="w-6 h-6 text-primary-500" />
                  <span>Price Trend</span>
                </h2>
              </div>
              {report.visualization_data.map((vizData) => (
                <div key={vizData.ticker}>
                  {vizData.price_history && vizData.price_history.length > 0 && (
                    <PriceChart data={vizData} viewMode="simple" />
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          {/* Detailed Mode: Full Report */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-8">
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {report.report}
              </ReactMarkdown>
            </div>
          </div>

          {/* Detailed Mode: All Charts */}
          {report.visualization_data && report.visualization_data.length > 0 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white flex items-center space-x-2">
                  <BarChart3 className="w-6 h-6 text-primary-500" />
                  <span>Interactive Charts</span>
                </h2>
              </div>

              {report.visualization_data.map((vizData) => (
                <div key={vizData.ticker} className="space-y-6">
                  {/* Price Chart */}
                  {vizData.price_history && vizData.price_history.length > 0 && (
                    <PriceChart data={vizData} viewMode={viewMode} />
                  )}

                  {/* Peer Comparison Chart */}
                  {vizData.peer_comparison && vizData.peer_comparison.length > 0 && (
                    <PeerComparisonChart data={vizData} viewMode={viewMode} />
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <p className="text-xs text-gray-500 text-center">
          This report was generated by AI agents and should not be considered as financial advice.
          Always conduct your own research and consult with a qualified financial advisor before making investment decisions.
        </p>
      </div>
    </div>
  );
}

interface DataIndicatorProps {
  icon: React.ElementType;
  label: string;
  agentName: string;
  available: boolean;
  error?: string;
  executed?: boolean;
}

function DataIndicator({ icon: Icon, label, agentName, available, error, executed }: DataIndicatorProps) {
  // Determine status: success, error, skipped, or not executed
  const getStatus = () => {
    if (!executed) return 'not_executed';  // Agent was not run at all
    if (error) return 'error';  // Agent ran but failed
    if (available) return 'success';  // Agent ran successfully and has data
    return 'skipped';  // Agent ran but no data (e.g., conditions not met)
  };

  const status = getStatus();

  const statusStyles = {
    success: {
      container: 'bg-success-950/20 border-success-800/50',
      icon: 'text-success-500',
      label: 'text-success-400',
      StatusIcon: CheckCircle2,
      statusColor: 'text-success-500'
    },
    error: {
      container: 'bg-error-950/20 border-error-800/50',
      icon: 'text-error-500',
      label: 'text-error-400',
      StatusIcon: XCircle,
      statusColor: 'text-error-500'
    },
    skipped: {
      container: 'bg-gray-900 border-gray-800',
      icon: 'text-gray-500',
      label: 'text-gray-500',
      StatusIcon: XCircle,
      statusColor: 'text-gray-600'
    },
    not_executed: {
      container: 'bg-gray-900 border-gray-800',
      icon: 'text-gray-600',
      label: 'text-gray-500',
      StatusIcon: XCircle,
      statusColor: 'text-gray-700'
    }
  };

  const style = statusStyles[status];
  const StatusIcon = style.StatusIcon;

  return (
    <div className={`flex items-center space-x-3 p-3 rounded-lg border ${style.container}`}>
      <Icon className={`w-5 h-5 flex-shrink-0 ${style.icon}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium truncate ${style.label}`}>
          {label}
        </p>
        {error && (
          <p className="text-xs text-error-400 truncate mt-0.5" title={error}>
            {error}
          </p>
        )}
        {!executed && (
          <p className="text-xs text-gray-600 truncate mt-0.5">
            Not executed
          </p>
        )}
      </div>
      <StatusIcon className={`w-4 h-4 ${style.statusColor} flex-shrink-0`} />
    </div>
  );
}

interface RoutingFlagProps {
  label: string;
  enabled: boolean;
}

function RoutingFlag({ label, enabled }: RoutingFlagProps) {
  return (
    <div
      className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium ${
        enabled
          ? 'bg-success-950/20 border border-success-800/50 text-success-400'
          : 'bg-gray-800 border border-gray-700 text-gray-500'
      }`}
    >
      {enabled ? (
        <CheckCircle2 className="w-3 h-3" />
      ) : (
        <XCircle className="w-3 h-3" />
      )}
      <span>{label}</span>
    </div>
  );
}

