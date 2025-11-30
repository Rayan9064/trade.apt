'use client';

import { useEffect, useState, useRef } from 'react';
import { useDecibel, DecibelCandle } from '@/context/DecibelContext';
import { Chart, registerables } from 'chart.js';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChartLine, 
  faArrowUp, 
  faArrowDown, 
  faCircle,
  faSync,
  faBolt
} from '@fortawesome/free-solid-svg-icons';

Chart.register(...registerables);

interface DecibelChartProps {
  symbol?: string;
  interval?: string;
  days?: number;
}

export default function DecibelChart({ 
  symbol = 'BTC', 
  interval = '1h',
  days = 1 
}: DecibelChartProps) {
  const { getPrice, fetchCandlesticks, isLoading: contextLoading, lastUpdate } = useDecibel();
  const [candles, setCandles] = useState<DecibelCandle[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedInterval, setSelectedInterval] = useState(interval);
  const [selectedDays, setSelectedDays] = useState(days);
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  const price = getPrice(selectedSymbol);

  // Fetch candlestick data
  useEffect(() => {
    const loadCandles = async () => {
      setIsLoading(true);
      const data = await fetchCandlesticks(selectedSymbol, selectedInterval, selectedDays);
      setCandles(data);
      setIsLoading(false);
    };
    loadCandles();
  }, [selectedSymbol, selectedInterval, selectedDays, fetchCandlesticks]);

  // Render chart
  useEffect(() => {
    if (!chartRef.current || candles.length === 0) return;

    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const labels = candles.map(c => {
      const date = new Date(c.time);
      return selectedDays <= 1 
        ? date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const prices = candles.map(c => c.close);
    const isPositive = prices.length > 1 && prices[prices.length - 1] >= prices[0];

    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `${selectedSymbol}/USD`,
          data: prices,
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
  }, [candles, selectedSymbol, selectedDays]);

  // Calculate price change
  const priceChange = candles.length > 1 
    ? ((candles[candles.length - 1].close - candles[0].close) / candles[0].close) * 100 
    : 0;
  const isPositiveChange = priceChange >= 0;

  const timeframeOptions = [
    { label: '1H', days: 1, interval: '1m' },
    { label: '1D', days: 1, interval: '15m' },
    { label: '1W', days: 7, interval: '1h' },
  ];

  const symbolOptions = ['BTC', 'ETH', 'SOL', 'APT', 'SUI', 'ARB'];

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
              <option key={s} value={s}>{s}-PERP</option>
            ))}
          </select>
          
          {/* Live Badge */}
          <div className="flex items-center gap-1.5 bg-green-500/10 px-2 py-1 rounded-full">
            <FontAwesomeIcon icon={faCircle} className="text-[6px] text-green-500 animate-pulse" />
            <span className="text-[10px] text-green-400 font-medium">DECIBEL LIVE</span>
          </div>
        </div>

        {/* Timeframe Selector */}
        <div className="flex space-x-1">
          {timeframeOptions.map((opt) => (
            <button
              key={opt.label}
              onClick={() => {
                setSelectedDays(opt.days);
                setSelectedInterval(opt.interval);
              }}
              className={`px-2 py-1 text-xs rounded transition ${
                selectedDays === opt.days && selectedInterval === opt.interval
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
      {price && (
        <div className="px-4 py-2 border-b border-gray-800 bg-gray-900/50">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-white">
                  ${price.mark_px.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </span>
                <span className={`text-sm font-medium flex items-center gap-1 ${
                  isPositiveChange ? 'text-green-400' : 'text-red-400'
                }`}>
                  <FontAwesomeIcon icon={isPositiveChange ? faArrowUp : faArrowDown} className="text-xs" />
                  {Math.abs(priceChange).toFixed(2)}%
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                Oracle: ${price.oracle_px.toLocaleString()} • Mid: ${price.mid_px.toLocaleString()}
              </div>
            </div>
            
            <div className="text-right">
              <div className="flex items-center gap-2 text-xs">
                <span className={`px-2 py-0.5 rounded ${
                  price.is_funding_positive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  Funding: {price.is_funding_positive ? '+' : '-'}{(price.funding_rate_bps / 100).toFixed(4)}%
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                OI: ${(price.open_interest / 1000000).toFixed(2)}M
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="flex-grow p-4 relative min-h-[300px]">
        {isLoading || contextLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <FontAwesomeIcon icon={faSync} className="text-2xl text-aptos-blue animate-spin" />
              <span className="text-sm text-gray-400">Loading Decibel data...</span>
            </div>
          </div>
        ) : candles.length === 0 ? (
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
          <span>Powered by Decibel.trade</span>
        </div>
        {lastUpdate && (
          <span>Updated: {lastUpdate.toLocaleTimeString()}</span>
        )}
      </div>
    </div>
  );
}
