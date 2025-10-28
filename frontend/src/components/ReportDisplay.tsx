import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Calendar, TrendingUp, Database, FileText, BarChart3, CheckCircle2, XCircle, Sparkles, FileStack } from 'lucide-react';
import { useState } from 'react';
import type { ResearchQueryResponse } from '../types';
import PriceChart from './Charts/PriceChart';
import PeerComparisonChart from './Charts/PeerComparisonChart';
import InvestorSnapshot from './InvestorSnapshot';

interface ReportDisplayProps {
  report: ResearchQueryResponse;
}

export default function ReportDisplay({ report }: ReportDisplayProps) {
  const [viewMode, setViewMode] = useState<'simple' | 'detailed'>('simple');
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

      {/* View Mode Toggle */}
      <div className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-primary-500" />
          <span className="text-sm text-gray-300">
            View Mode / 查看模式
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
            <span>Simple / 简单</span>
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
            <span>Detailed / 详细</span>
          </button>
        </div>
      </div>

      {/* Data Availability Indicators */}
      {viewMode === 'detailed' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <DataIndicator
            icon={TrendingUp}
            label="Market Data"
            available={report.market_data_available}
          />
          <DataIndicator
            icon={FileText}
            label="Sentiment"
            available={report.sentiment_available}
          />
          <DataIndicator
            icon={BarChart3}
            label="Analyst Consensus"
            available={report.analyst_consensus_available}
          />
          <DataIndicator
            icon={Database}
            label={`Context Retrieved (${report.context_retrieved})`}
            available={report.context_retrieved > 0}
          />
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
                  <span>Price Trend / 价格走势</span>
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
                  <span>Interactive Charts / 交互式图表</span>
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
        <p className="text-xs text-gray-500 text-center mt-2">
          本报告由AI代理生成，不应被视为财务建议。
          在做出投资决策之前，请务必进行自己的研究并咨询合格的财务顾问。
        </p>
      </div>
    </div>
  );
}

interface DataIndicatorProps {
  icon: React.ElementType;
  label: string;
  available: boolean;
}

function DataIndicator({ icon: Icon, label, available }: DataIndicatorProps) {
  return (
    <div className={`flex items-center space-x-3 p-3 rounded-lg border ${
      available
        ? 'bg-success-950/20 border-success-800/50'
        : 'bg-gray-900 border-gray-800'
    }`}>
      <Icon className={`w-5 h-5 flex-shrink-0 ${
        available ? 'text-success-500' : 'text-gray-600'
      }`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium truncate ${
          available ? 'text-success-400' : 'text-gray-500'
        }`}>
          {label}
        </p>
      </div>
      {available ? (
        <CheckCircle2 className="w-4 h-4 text-success-500 flex-shrink-0" />
      ) : (
        <XCircle className="w-4 h-4 text-gray-600 flex-shrink-0" />
      )}
    </div>
  );
}
