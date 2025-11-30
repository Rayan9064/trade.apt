'use client';

import { usePrices } from '@/context/PriceContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircle, faArrowUp, faArrowDown } from '@fortawesome/free-solid-svg-icons';

const TRACKED_TOKENS = ['BTC', 'ETH', 'SOL', 'APT', 'BNB', 'XRP', 'DOGE'];

export default function LivePriceTicker() {
  const { isConnected, getFormattedPrice, getPriceChange } = usePrices();

  return (
    <div className="bg-gray-900/80 border-b border-gray-800 px-4 py-2 overflow-hidden">
      <div className="flex items-center gap-6 animate-scroll">
        {/* Connection Status */}
        <div className="flex items-center gap-2 text-xs shrink-0">
          <FontAwesomeIcon 
            icon={faCircle} 
            className={`text-[8px] ${isConnected ? 'text-green-500 animate-pulse' : 'text-red-500'}`} 
          />
          <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
            {isConnected ? 'LIVE' : 'Connecting...'}
          </span>
        </div>

        {/* Price Ticker */}
        <div className="flex items-center gap-6 overflow-x-auto scrollbar-hide">
          {TRACKED_TOKENS.map((symbol) => {
            const change = getPriceChange(symbol);
            const isPositive = change >= 0;
            
            return (
              <div key={symbol} className="flex items-center gap-2 shrink-0">
                <span className="text-gray-400 text-xs font-medium">{symbol}</span>
                <span className={`text-sm font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {getFormattedPrice(symbol)}
                </span>
                <span className={`text-xs flex items-center gap-0.5 ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                  <FontAwesomeIcon icon={isPositive ? faArrowUp : faArrowDown} className="text-[8px]" />
                  {Math.abs(change).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
