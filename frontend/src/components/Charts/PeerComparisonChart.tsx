import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { BarChart3, Info } from 'lucide-react';
import type { VisualizationData } from '../../types';
import FinancialTermTooltip from '../FinancialTermTooltip';

interface PeerComparisonChartProps {
  data: VisualizationData;
  viewMode?: 'simple' | 'detailed';
}

export default function PeerComparisonChart({ data, viewMode = 'simple' }: PeerComparisonChartProps) {
  // Check if we have peer comparison data
  if (!data.peer_comparison || data.peer_comparison.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2 mb-4">
          <BarChart3 className="w-5 h-5 text-primary-500" />
          <span>Peer Valuation Comparison</span>
        </h3>
        <div className="text-center py-8 text-gray-500">
          <p>No peer comparison data available</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = data.peer_comparison.map(peer => ({
    name: peer.ticker,
    fullName: peer.name,
    'P/E Ratio': peer.pe_ratio,
    'P/B Ratio': peer.pb_ratio,
    'P/S Ratio': peer.ps_ratio,
    isMain: peer.is_main,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 border border-gray-700 p-3 rounded-lg shadow-lg">
          <p className="text-sm font-semibold text-white mb-2">{data.fullName}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-xs text-gray-400">
              {entry.name}: {entry.value !== null ? entry.value.toFixed(2) : 'N/A'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Colors for main ticker vs peers
  const getBarColor = (isMain: boolean) => isMain ? '#3b82f6' : '#6b7280';

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2 mb-4">
          <BarChart3 className="w-5 h-5 text-primary-500" />
          <span>Peer Valuation Comparison</span>
        </h3>

        {/* Info banner for beginners (Simple mode only) */}
        {viewMode === 'simple' && (
          <div className="flex items-start space-x-2 p-3 bg-primary-950/20 border border-primary-900/50 rounded-lg">
            <Info className="w-4 h-4 text-primary-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-gray-400">
              <p className="mb-2">
                <span className="text-primary-400 font-medium">For beginners:</span>
              </p>
              <p className="mb-2">
                These ratios help compare how "expensive" or "cheap" a stock is relative to its peers.
                Lower numbers generally mean better value, but context matters!
              </p>
              <p className="flex items-center space-x-4">
                <span className="flex items-center space-x-1">
                  <span className="inline-block w-2 h-2 bg-primary-500 rounded"></span>
                  <span className="text-primary-400">Blue = Target Stock</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="inline-block w-2 h-2 bg-gray-500 rounded"></span>
                  <span className="text-gray-400">Gray = Peers</span>
                </span>
              </p>
            </div>
          </div>
        )}

        {/* Detailed info (Detailed mode only) */}
        {viewMode === 'detailed' && (
          <div className="flex items-start space-x-2 p-3 bg-primary-950/20 border border-primary-900/50 rounded-lg">
            <Info className="w-4 h-4 text-primary-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-gray-400">
              <ul className="space-y-1 list-disc list-inside">
                <li><strong>P/E Ratio:</strong> Price ÷ Earnings. Lower is typically cheaper, but growth stocks may have high P/E.</li>
                <li><strong>P/B Ratio:</strong> Price ÷ Book Value. Below 1.0 may indicate undervaluation.</li>
                <li><strong>P/S Ratio:</strong> Price ÷ Sales. Useful for companies without profits yet.</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* P/E Ratio Chart */}
      <div className="mb-8">
        <FinancialTermTooltip term="P/E" showIcon={false}>
          <h4 className="text-sm font-medium text-gray-300 mb-3 cursor-help inline-block">
            P/E Ratio (Price-to-Earnings)
          </h4>
        </FinancialTermTooltip>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="name"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="P/E Ratio" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.isMain)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* P/B Ratio Chart */}
      <div className="mb-8">
        <FinancialTermTooltip term="P/B" showIcon={false}>
          <h4 className="text-sm font-medium text-gray-300 mb-3 cursor-help inline-block">
            P/B Ratio (Price-to-Book)
          </h4>
        </FinancialTermTooltip>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="name"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="P/B Ratio" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.isMain)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* P/S Ratio Chart */}
      <div>
        <FinancialTermTooltip term="P/S" showIcon={false}>
          <h4 className="text-sm font-medium text-gray-300 mb-3 cursor-help inline-block">
            P/S Ratio (Price-to-Sales)
          </h4>
        </FinancialTermTooltip>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="name"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="P/S Ratio" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.isMain)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center space-x-6 text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-primary-500 rounded"></div>
          <span className="text-gray-400">Target Stock</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-gray-500 rounded"></div>
          <span className="text-gray-400">Sector Average</span>
        </div>
      </div>
    </div>
  );
}
