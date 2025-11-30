'use client';

import { useEffect, useState, useRef } from 'react';
import { usePrices } from '@/context/PriceContext';
import { Chart, registerables } from 'chart.js';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faArrowUp, 
  faArrowDown, 
  faCircle,
  faSync,
  faBolt,
  faChartLine
} from '@fortawesome/free-solid-svg-icons';

Chart.register(...registerables);

interface LiveChartProps {
  symbol?: string;
}

interface ChartDataResponse {
  symbol: string;
  prices: Array<{ time: number; value: number }>;
  stats: {
    current: number;
    open: number;
    high: number;
    low: number;
    change: number;
    change_percent: number;
    period: string;
  } | null;
  days: number;
  source?: string;
}

// Use relative API routes for Next.js
const API_URL = '/api';

export default function LiveChart({ symbol = 'BTC' }: LiveChartProps) {
  const { getPrice, getPriceChange, getFormattedPrice, isConnected } = usePrices();
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDays, setSelectedDays] = useState(1);
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  // Get live price from context
  const livePrice = getPrice(selectedSymbol);
  const priceChange = getPriceChange(selectedSymbol);

  // Update symbol when prop changes
  useEffect(() => {
    setSelectedSymbol(symbol);
  }, [symbol]);

  // Fetch chart data from backend
  useEffect(() => {
    const fetchChartData = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`${API_URL}/chart/${selectedSymbol}?days=${selectedDays}`);
        if (!response.ok) throw new Error('Failed to fetch chart data');
        const data = await response.json();
        setChartData(data);
      } catch (err) {
        console.error('Error fetching chart data:', err);
        setChartData(null);
      } finally {
        setIsLoading(false);
      }
    };
    fetchChartData();
  }, [selectedSymbol, selectedDays]);

  // Render chart
  useEffect(() => {
    if (!chartRef.current || !chartData?.prices || chartData.prices.length === 0) return;

    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const prices = chartData.prices;
    const labels = prices.map(p => {
      const date = new Date(p.time);
      return selectedDays <= 1 
        ? date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const priceValues = prices.map(p => p.value);
    const isPositive = priceValues.length > 1 && priceValues[priceValues.length - 1] >= priceValues[0];

    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `${selectedSymbol}/USDT`,
          data: priceValues,
          borderColor: isPositive ? '#10B981' : '#EF4444',
          backgroundColor: isPositive 
            ? 'rgba(16, 185, 129, 0.1)' 
            : 'rgba(239, 68, 68, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: isPositive ? '#10B981' : '#EF4444',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            padding: 12,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              label: (context) => `$${(context.parsed.y ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
            },
          },
        },
        scales: {
          x: { 
            display: true,
            grid: { display: false },
            ticks: { 
              color: '#6B7280',
              maxTicksLimit: 6,
              font: { size: 10 }
            }
          },
          y: { 
            position: 'right',
            grid: { color: '#1F2937' },
            ticks: { 
              color: '#9CA3AF',
              callback: (value) => `$${Number(value).toLocaleString()}`,
              font: { size: 10 }
            }
          },
        },
        interaction: {
          mode: 'index',
          intersect: false,
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [chartData, selectedSymbol, selectedDays]);

  const isPositiveChange = priceChange >= 0;

  const timeframeOptions = [
    { label: '24H', days: 1 },
    { label: '7D', days: 7 },
    { label: '30D', days: 30 },
    { label: '90D', days: 90 },
  ];

  const symbolOptions = ['BTC', 'ETH', 'SOL', 'APT', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT'];

  return (
    <div className="bg-bg-panel border border-gray-800 rounded-xl flex flex-col shadow-lg h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div className="flex items-center gap-3">
          {/* Symbol Selector */}
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white text-sm font-bold rounded-lg px-3 py-1.5 focus:outline-none focus:border-aptos-blue"
          >
            {symbolOptions.map(s => (
              <option key={s} value={s}>{s}/USDT</option>
            ))}
          </select>
          
          {/* Live Badge */}
          <div className="flex items-center gap-1.5 bg-green-500/10 px-2 py-1 rounded-full">
            <FontAwesomeIcon icon={faCircle} className={`text-[6px] ${isConnected ? 'text-green-500 animate-pulse' : 'text-red-500'}`} />
            <span className={`text-[10px] font-medium ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>

        {/* Timeframe Selector */}
        <div className="flex space-x-1">
          {timeframeOptions.map((opt) => (
            <button
              key={opt.label}
              onClick={() => setSelectedDays(opt.days)}
              className={`px-2 py-1 text-xs rounded transition ${
                selectedDays === opt.days
                  ? 'bg-aptos-blue text-white'
                  : 'text-gray-500 hover:text-white hover:bg-gray-800'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Price Info */}
      <div className="px-4 py-2 border-b border-gray-800 bg-gray-900/50">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-white">
                {livePrice ? `$${livePrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : getFormattedPrice(selectedSymbol)}
              </span>
              <span className={`text-sm font-medium flex items-center gap-1 ${
                isPositiveChange ? 'text-green-400' : 'text-red-400'
              }`}>
                <FontAwesomeIcon icon={isPositiveChange ? faArrowUp : faArrowDown} className="text-xs" />
                {Math.abs(priceChange).toFixed(2)}%
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {selectedSymbol}/USDT • Spot
            </div>
          </div>
          
          {chartData?.stats && (
            <div className="text-right text-xs">
              <div className="flex gap-4">
                <div>
                  <span className="text-gray-500">H: </span>
                  <span className="text-green-400">${chartData.stats.high.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                </div>
                <div>
                  <span className="text-gray-500">L: </span>
                  <span className="text-red-400">${chartData.stats.low.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-grow p-4 relative min-h-[300px]">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <FontAwesomeIcon icon={faSync} className="text-2xl text-aptos-blue animate-spin" />
              <span className="text-sm text-gray-400">Loading chart data...</span>
            </div>
          </div>
        ) : !chartData?.prices || chartData.prices.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <FontAwesomeIcon icon={faChartLine} className="text-4xl text-gray-600 mb-2" />
              <p className="text-gray-400 text-sm">No chart data available</p>
            </div>
          </div>
        ) : (
          <canvas ref={chartRef}></canvas>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-800 bg-gray-900/30 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <FontAwesomeIcon icon={faBolt} className="text-yellow-500" />
          <span>Real-time prices via Decibel</span>
        </div>
        <span>Chart data: {chartData?.source || 'Decibel'}</span>
      </div>
    </div>
  );
}
