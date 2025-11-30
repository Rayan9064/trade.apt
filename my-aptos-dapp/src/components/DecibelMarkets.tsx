'use client';

import { useDecibel } from '@/context/DecibelContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faArrowUp, 
  faArrowDown, 
  faCircle,
  faFire,
  faBolt
} from '@fortawesome/free-solid-svg-icons';

interface DecibelMarketsProps {
  onSelectSymbol?: (symbol: string) => void;
  selectedSymbol?: string;
}

export default function DecibelMarkets({ onSelectSymbol, selectedSymbol }: DecibelMarketsProps) {
  const { markets, prices, isLoading, error, lastUpdate } = useDecibel();

  // Sort by open interest (most popular first)
  const sortedMarkets = [...markets].sort((a, b) => {
    const priceA = prices[a.symbol];
    const priceB = prices[b.symbol];
    return (priceB?.open_interest || 0) - (priceA?.open_interest || 0);
  });

  if (isLoading) {
    return (
      <div className="bg-bg-panel border border-gray-800 rounded-xl p-4">
        <div className="flex items-center justify-center h-32">
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-aptos-blue border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-gray-400">Loading Decibel markets...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-bg-panel border border-gray-800 rounded-xl p-4">
        <div className="text-center text-red-400 text-sm">
          <p>Failed to load Decibel markets</p>
          <p className="text-xs text-gray-500 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-bg-panel border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900/50">
        <div className="flex items-center gap-2">
          <FontAwesomeIcon icon={faFire} className="text-orange-500" />
          <h3 className="text-sm font-bold text-white">Decibel Perpetuals</h3>
          <span className="text-xs bg-aptos-blue/20 text-aptos-blue px-2 py-0.5 rounded-full">
            {markets.length} Markets
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <FontAwesomeIcon icon={faCircle} className="text-[6px] text-green-500 animate-pulse" />
          <span className="text-[10px] text-green-400">LIVE</span>
        </div>
      </div>

      {/* Market List */}
      <div className="max-h-[400px] overflow-y-auto">
        {sortedMarkets.map((market) => {
          const price = prices[market.symbol];
          const isSelected = selectedSymbol === market.symbol;
          
          return (
            <div
              key={market.market_addr}
              onClick={() => onSelectSymbol?.(market.symbol)}
              className={`flex items-center justify-between px-4 py-3 border-b border-gray-800/50 cursor-pointer transition-all hover:bg-gray-800/50 ${
                isSelected ? 'bg-aptos-blue/10 border-l-2 border-l-aptos-blue' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  isSelected ? 'bg-aptos-blue text-white' : 'bg-gray-800 text-gray-300'
                }`}>
                  {market.symbol.slice(0, 2)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">{market.market_name}</span>
                    <span className="text-[10px] bg-yellow-500/20 text-yellow-400 px-1.5 py-0.5 rounded">
                      {market.max_leverage}x
                    </span>
                  </div>
                  {price && (
                    <div className="text-xs text-gray-500">
                      OI: ${(price.open_interest / 1000000).toFixed(2)}M
                    </div>
                  )}
                </div>
              </div>

              {price ? (
                <div className="text-right">
                  <div className="text-sm font-bold text-white">
                    ${price.mark_px.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </div>
                  <div className={`text-xs flex items-center justify-end gap-1 ${
                    price.is_funding_positive ? 'text-green-400' : 'text-red-400'
                  }`}>
                    <FontAwesomeIcon 
                      icon={price.is_funding_positive ? faArrowUp : faArrowDown} 
                      className="text-[8px]" 
                    />
                    <span>
                      {price.is_funding_positive ? '+' : ''}{(price.funding_rate_bps / 100).toFixed(4)}%
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-gray-500">Loading...</div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-800 bg-gray-900/30 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <FontAwesomeIcon icon={faBolt} className="text-yellow-500" />
          <span>Decibel.trade</span>
        </div>
        {lastUpdate && (
          <span>Updated: {lastUpdate.toLocaleTimeString()}</span>
        )}
      </div>
    </div>
  );
}
