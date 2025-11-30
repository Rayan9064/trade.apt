'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
);

interface PricePoint {
  time: number;
  value: number;
}

interface OHLCVPoint {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartStats {
  current: number;
  open: number;
  high: number;
  low: number;
  change: number;
  change_percent: number;
  period: string;
}

interface ChartData {
  symbol: string;
  prices: PricePoint[];
  ohlcv?: OHLCVPoint[];
  stats: ChartStats | null;
  days: number;
  interval?: string;
  data_points: number;
  source?: string;
  last_updated?: string;
}

interface CoinChartProps {
  symbol: string;
  onClose: () => void;
}

const timeframeOptions = [
  { label: '24H', value: 1 },
  { label: '7D', value: 7 },
  { label: '30D', value: 30 },
  { label: '90D', value: 90 },
  { label: '1Y', value: 365 },
];

const CoinChart: React.FC<CoinChartProps> = ({ symbol, onClose }) => {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState(7);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchChartData = useCallback(async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chart/${symbol}?days=${timeframe}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch chart data for ${symbol}`);
      }

      const data: ChartData = await response.json();
      setChartData(data);
      setLastUpdateTime(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chart');
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchChartData();
      setLoading(false);
    };

    loadData();

    // Set up auto-refresh every 30 seconds for real-time updates
    refreshIntervalRef.current = setInterval(() => {
      fetchChartData();
    }, 30000);

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [fetchChartData]);

  const formatPrice = (price: number) => {
    if (price >= 1000) {
      return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (price >= 1) {
      return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
    }
    return price.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 8 });
  };

  const stats = chartData?.stats;
  const isPositive = stats ? stats.change_percent >= 0 : true;
  const dataSource = chartData?.source || 'unknown';

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        padding: 12,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          title: (context: any) => {
            const date = new Date(context[0].parsed.x);
            return date.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });
          },
          label: (context: any) => {
            return `$${formatPrice(context.parsed.y)}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: timeframe <= 1 ? 'hour' as const : timeframe <= 7 ? 'day' as const : 'week' as const,
          displayFormats: {
            hour: 'HH:mm',
            day: 'MMM d',
            week: 'MMM d',
          },
        },
        grid: {
          display: false,
        },
        ticks: {
          color: '#9ca3af',
          maxTicksLimit: 6,
        },
      },
      y: {
        position: 'right' as const,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#9ca3af',
          callback: (value: any) => `$${formatPrice(value)}`,
        },
      },
    },
  };

  const getChartDataConfig = () => {
    if (!chartData || !chartData.prices || chartData.prices.length === 0) return null;

    const lineColor = isPositive ? '#10B981' : '#EF4444';
    const gradientColor = isPositive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';

    return {
      labels: chartData.prices.map((p) => p.time),
      datasets: [
        {
          label: symbol,
          data: chartData.prices.map((p) => ({
            x: p.time,
            y: p.value,
          })),
          borderColor: lineColor,
          backgroundColor: gradientColor,
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: lineColor,
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
        },
      ],
    };
  };

  const getSourceBadge = () => {
    if (dataSource === 'decibel') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-500/20 text-green-400 border border-green-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
          Decibel Live
        </span>
      );
    } else if (dataSource === 'coingecko') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-orange-500/20 text-orange-400 border border-orange-500/30">
          CoinGecko
        </span>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
            {symbol.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-white font-semibold text-lg">{symbol}/USD</h3>
              {getSourceBadge()}
            </div>
            {stats && (
              <div className="flex items-center gap-2">
                <span className="text-white text-xl font-bold">
                  ${formatPrice(stats.current)}
                </span>
                <span
                  className={`text-sm font-medium ${
                    isPositive ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {isPositive ? '+' : ''}
                  {stats.change_percent.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {lastUpdateTime && (
            <span className="text-xs text-gray-500">
              Updated {lastUpdateTime.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Timeframe Selector */}
      <div className="flex items-center justify-between p-3 border-b border-gray-800">
        <div className="flex gap-1">
          {timeframeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setTimeframe(option.value)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                timeframe === option.value
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        {chartData?.interval && (
          <span className="text-xs text-gray-500">
            Interval: {chartData.interval}
          </span>
        )}
      </div>

      {/* Chart Area */}
      <div className="flex-1 p-4 min-h-[300px]">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-gray-400 text-sm">Loading chart data from Decibel...</span>
            </div>
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-red-400 text-4xl mb-3">📊</div>
              <p className="text-gray-400">{error}</p>
              <button
                onClick={() => {
                  setLoading(true);
                  fetchChartData().finally(() => setLoading(false));
                }}
                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : chartData && getChartDataConfig() ? (
          <Line options={chartOptions} data={getChartDataConfig()!} />
        ) : null}
      </div>

      {/* Stats Footer */}
      {stats && !loading && !error && (
        <div className="grid grid-cols-4 gap-2 p-3 border-t border-gray-800 bg-gray-950/50">
          <div className="text-center">
            <p className="text-gray-500 text-xs">High</p>
            <p className="text-green-400 font-medium">
              ${formatPrice(stats.high)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500 text-xs">Low</p>
            <p className="text-red-400 font-medium">
              ${formatPrice(stats.low)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500 text-xs">Open</p>
            <p className="text-white font-medium">
              ${formatPrice(stats.open)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500 text-xs">Change</p>
            <p className={`font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {isPositive ? '+' : ''}${formatPrice(Math.abs(stats.change))}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default CoinChart;
