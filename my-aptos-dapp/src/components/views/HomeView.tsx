'use client';

import { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleChevronDown, faCircleChevronUp, faCircleMinus } from '@fortawesome/free-solid-svg-icons';

Chart.register(...registerables);

export default function HomeView() {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // Destroy previous chart
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const labels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const dataPoints = labels.map(() => 67000 + Math.random() * 3000);

    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'BTC/USD Price',
            data: dataPoints,
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { display: false },
          y: { grid: { color: '#1F2937' }, ticks: { color: '#9CA3AF' } },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-[600px]">
      {/* CHARTS (Large Left) */}
      <div className="lg:col-span-8 bg-bg-panel border border-gray-800 rounded-xl p-1 flex flex-col shadow-lg">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <h3 className="font-bold text-sm text-white">BTC/USD Live Chart</h3>
          <div className="flex space-x-2">
            <button className="px-2 py-1 text-xs bg-aptos-blue text-white rounded">1H</button>
            <button className="px-2 py-1 text-xs text-gray-500 hover:text-white transition">1D</button>
            <button className="px-2 py-1 text-xs text-gray-500 hover:text-white transition">1W</button>
          </div>
        </div>
        <div className="chart-container bg-black/40 flex-grow relative">
          <canvas ref={chartRef}></canvas>
        </div>
      </div>

      {/* PORTFOLIO WITH SHORT PREDICTIONS (Smaller Right) */}
      <div className="lg:col-span-4 flex flex-col gap-6">
        <div className="bg-bg-panel border border-gray-800 rounded-xl p-6 shadow-lg">
          <h3 className="font-bold text-sm text-gray-400 uppercase mb-4">Portfolio Overview</h3>
          <div className="flex items-baseline mb-6">
            <span className="text-3xl font-bold text-white">$14,250.80</span>
            <span className="ml-3 text-sm text-green-400 bg-green-900/20 px-2 py-0.5 rounded">+4.2% (24H)</span>
          </div>

          <h4 className="text-xs font-bold text-aptos-blue uppercase border-b border-gray-800 pb-2 mb-3">
            AI Short Predictions
          </h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center text-red-400">
              <span>
                <FontAwesomeIcon icon={faCircleChevronDown} className="mr-2" />
                ETH
              </span>
              <span className="font-bold">Short-term Bearish</span>
            </div>
            <div className="flex justify-between items-center text-green-400">
              <span>
                <FontAwesomeIcon icon={faCircleChevronUp} className="mr-2" />
                SOL
              </span>
              <span className="font-bold">Slightly Bullish</span>
            </div>
            <div className="flex justify-between items-center text-gray-400">
              <span>
                <FontAwesomeIcon icon={faCircleMinus} className="mr-2" />
                XRP
              </span>
              <span className="font-bold">Neutral (Hold)</span>
            </div>
          </div>

          <button className="mt-6 w-full py-2 bg-aptos-blue text-white font-bold rounded-lg text-sm hover:bg-blue-600 transition">
            View Full Portfolio
          </button>
        </div>
      </div>
    </div>
  );
}
