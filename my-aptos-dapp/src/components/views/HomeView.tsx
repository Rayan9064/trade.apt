'use client';

import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleChevronDown, faCircleChevronUp, faCircleMinus, faBolt } from '@fortawesome/free-solid-svg-icons';
import LiveChart from '@/components/LiveChart';
import SpotMarkets from '@/components/SpotMarkets';

export default function HomeView() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-[600px]">
      {/* CHARTS (Large Left) */}
      <div className="lg:col-span-8 flex flex-col gap-4">
        {/* Live Chart */}
        <div className="flex-grow min-h-[400px]">
          <LiveChart symbol={selectedSymbol} />
        </div>
      </div>

      {/* RIGHT SIDEBAR */}
      <div className="lg:col-span-4 flex flex-col gap-4">
        {/* Spot Markets */}
        <SpotMarkets 
          selectedSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
        />

        {/* AI Predictions Card */}
        <div className="bg-bg-panel border border-gray-800 rounded-xl p-4 shadow-lg">
          <h4 className="text-xs font-bold text-aptos-blue uppercase border-b border-gray-800 pb-2 mb-3 flex items-center gap-2">
            <FontAwesomeIcon icon={faBolt} className="text-yellow-500" />
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
        </div>
      </div>
    </div>
  );
}
