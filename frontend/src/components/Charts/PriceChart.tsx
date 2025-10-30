import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { format, parseISO } from 'date-fns';
import { TrendingUp, TrendingDown, Info } from 'lucide-react';
import type { VisualizationData } from '../../types';
import FinancialTermTooltip from '../FinancialTermTooltip';

interface PriceChartProps {
  data: VisualizationData;
  viewMode?: 'simple' | 'detailed';
}

export default function PriceChart({ data, viewMode = 'simple' }: PriceChartProps) {
  // Format price history for chart
  const chartData = data.price_history.map(point => ({
    date: format(parseISO(point.date), 'MMM dd'),
    fullDate: format(parseISO(point.date), 'yyyy-MM-dd'),
    price: point.close,
    high: point.high,
    low: point.low,
    volume: point.volume,
  }));

  // Calculate price change
  const firstPrice = data.price_history[0]?.close;
  const lastPrice = data.price_history[data.price_history.length - 1]?.close;
  const priceChange = lastPrice && firstPrice ? ((lastPrice - firstPrice) / firstPrice) * 100 : 0;
  const isPositive = priceChange >= 0;

  // Format numbers
  const formatPrice = (value: number) => `$${value.toFixed(2)}`;
  const formatVolume = (value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toString();
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 border border-gray-700 p-3 rounded-lg shadow-lg">
          <p className="text-xs text-gray-400 mb-1">{data.fullDate}</p>
          <p className="text-sm font-semibold text-white">Price: {formatPrice(data.price)}</p>
          <p className="text-xs text-gray-400">High: {formatPrice(data.high)}</p>
          <p className="text-xs text-gray-400">Low: {formatPrice(data.low)}</p>
          <p className="text-xs text-gray-400 mt-1">Volume: {formatVolume(data.volume)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-primary-500" />
            <span>{data.ticker} Price Trend</span>
          </h3>
          <div className={`flex items-center space-x-1 px-3 py-1 rounded-full border ${
            isPositive
              ? 'bg-success-950/30 text-success-400 border-success-800/50'
              : 'bg-error-950/30 text-error-400 border-error-800/50'
          }`}>
            {isPositive ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span className="text-sm font-semibold">
              {isPositive ? '+' : ''}{priceChange.toFixed(2)}%
            </span>
            <span className="text-xs opacity-75">
              {isPositive ? 'Bullish' : 'Bearish'}
            </span>
          </div>
        </div>

        {/* 52-week position indicator */}
        {data.week_52_high && data.week_52_low && data.current_position_pct !== null && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <FinancialTermTooltip term="52-Week High">
                <span className="cursor-help">
                  52-Week Range
                </span>
              </FinancialTermTooltip>
              <span>Current Position: {data.current_position_pct.toFixed(1)}%</span>
            </div>
            <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="absolute h-full bg-gradient-to-r from-error-500 via-warning-500 to-success-500"
                style={{ width: '100%' }}
              />
              <div
                className="absolute w-1 h-full bg-white shadow-lg"
                style={{ left: `${data.current_position_pct}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{formatPrice(data.week_52_low)}</span>
              <span>{formatPrice(data.week_52_high)}</span>
            </div>
          </div>
        )}

        {/* Info banner for beginners (Simple mode only) */}
        {viewMode === 'simple' && (
          <div className="mt-4 flex items-start space-x-2 p-3 bg-primary-950/20 border border-primary-900/50 rounded-lg">
            <Info className="w-4 h-4 text-primary-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-gray-400 space-y-1">
              <p>
                <span className="text-primary-400 font-medium">For beginners:</span>
                {' '}The chart shows the stock's closing price over the past year.
              </p>
              <p className="flex items-center space-x-4">
                <span className="flex items-center space-x-1">
                  <span className="inline-block w-2 h-2 bg-success-500 rounded-full"></span>
                  <span className="text-success-400">Green = Bullish</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="inline-block w-2 h-2 bg-error-500 rounded-full"></span>
                  <span className="text-error-400">Red = Bearish</span>
                </span>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickFormatter={(value) => value}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickFormatter={formatPrice}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />

          {/* 52-week high reference line */}
          {data.week_52_high && (
            <ReferenceLine
              y={data.week_52_high}
              stroke="#10b981"
              strokeDasharray="3 3"
              label={{ value: '52W High', position: 'right', fill: '#10b981', fontSize: 11 }}
            />
          )}

          {/* 52-week low reference line */}
          {data.week_52_low && (
            <ReferenceLine
              y={data.week_52_low}
              stroke="#ef4444"
              strokeDasharray="3 3"
              label={{ value: '52W Low', position: 'right', fill: '#ef4444', fontSize: 11 }}
            />
          )}

          <Area
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPrice)"
            name="Closing Price"
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Summary stats */}
      {viewMode === 'detailed' && (data.period_high || data.period_low || data.average_volume) && (
        <div className="mt-6 grid grid-cols-3 gap-4">
          {data.period_high && (
            <div className="text-center p-3 bg-gray-800/50 rounded-lg border border-success-800/30">
              <FinancialTermTooltip term="52-Week High" showIcon={false}>
                <p className="text-xs text-gray-500 mb-1 cursor-help">Period High</p>
              </FinancialTermTooltip>
              <p className="text-sm font-semibold text-success-400">{formatPrice(data.period_high)}</p>
            </div>
          )}
          {data.period_low && (
            <div className="text-center p-3 bg-gray-800/50 rounded-lg border border-error-800/30">
              <FinancialTermTooltip term="52-Week Low" showIcon={false}>
                <p className="text-xs text-gray-500 mb-1 cursor-help">Period Low</p>
              </FinancialTermTooltip>
              <p className="text-sm font-semibold text-error-400">{formatPrice(data.period_low)}</p>
            </div>
          )}
          {data.average_volume && (
            <div className="text-center p-3 bg-gray-800/50 rounded-lg border border-gray-700">
              <FinancialTermTooltip term="Volume" showIcon={false}>
                <p className="text-xs text-gray-500 mb-1 cursor-help">Avg Volume</p>
              </FinancialTermTooltip>
              <p className="text-sm font-semibold text-white">{formatVolume(data.average_volume)}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
