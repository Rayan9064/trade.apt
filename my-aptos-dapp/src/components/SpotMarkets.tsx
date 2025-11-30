'use client';

import { usePrices } from '@/context/PriceContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faArrowUp, 
  faArrowDown, 
  faCircle,
  faFire,
  faBolt
} from '@fortawesome/free-solid-svg-icons';

interface SpotMarketsProps {
  onSelectSymbol?: (symbol: string) => void;
  selectedSymbol?: string;
}

// Top trading pairs
const SPOT_MARKETS = [
  { symbol: 'BTC', name: 'Bitcoin', color: '#F7931A' },
  { symbol: 'ETH', name: 'Ethereum', color: '#627EEA' },
  { symbol: 'SOL', name: 'Solana', color: '#00FFA3' },
  { symbol: 'APT', name: 'Aptos', color: '#4CC9F0' },
  { symbol: 'BNB', name: 'BNB', color: '#F0B90B' },
  { symbol: 'XRP', name: 'Ripple', color: '#23292F' },
  { symbol: 'ADA', name: 'Cardano', color: '#0033AD' },
  { symbol: 'DOGE', name: 'Dogecoin', color: '#C2A633' },
  { symbol: 'AVAX', name: 'Avalanche', color: '#E84142' },
  { symbol: 'DOT', name: 'Polkadot', color: '#E6007A' },
];

export default function SpotMarkets({ onSelectSymbol, selectedSymbol }: SpotMarketsProps) {
  const { prices, isConnected, getPrice, getPriceChange, getFormattedPrice } = usePrices();

  // Sort by 24h volume (if available) or just use default order
  const sortedMarkets = [...SPOT_MARKETS].sort((a, b) => {
    const priceA = prices[a.symbol];
    const priceB = prices[b.symbol];
    return (priceB?.volume_24h || 0) - (priceA?.volume_24h || 0);
  });

  return (
    <div className="bg-bg-panel border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900/50">
        <div className="flex items-center gap-2">
          <FontAwesomeIcon icon={faFire} className="text-orange-500" />
          <h3 className="text-sm font-bold text-white">Spot Markets</h3>
          <span className="text-xs bg-aptos-blue/20 text-aptos-blue px-2 py-0.5 rounded-full">
            USDT Pairs
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <FontAwesomeIcon icon={faCircle} className={`text-[6px] ${isConnected ? 'text-green-500 animate-pulse' : 'text-red-500'}`} />
          <span className={`text-[10px] ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Market List */}
      <div className="max-h-[350px] overflow-y-auto">
        {sortedMarkets.map((market) => {
          const price = getPrice(market.symbol);
          const change = getPriceChange(market.symbol);
          const isSelected = selectedSymbol === market.symbol;
          const isPositive = change >= 0;
          
          return (
            <div
              key={market.symbol}
              onClick={() => onSelectSymbol?.(market.symbol)}
              className={`flex items-center justify-between px-4 py-3 border-b border-gray-800/50 cursor-pointer transition-all hover:bg-gray-800/50 ${
                isSelected ? 'bg-aptos-blue/10 border-l-2 border-l-aptos-blue' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
                  style={{ backgroundColor: market.color + '30', border: `1px solid ${market.color}` }}
                >
                  {market.symbol.slice(0, 2)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">{market.symbol}/USDT</span>
                  </div>
                  <span className="text-xs text-gray-500">{market.name}</span>
                </div>
              </div>

              <div className="text-right">
                <div className="text-sm font-bold text-white">
                  {price ? `$${price.toLocaleString(undefined, { maximumFractionDigits: price < 1 ? 6 : 2 })}` : getFormattedPrice(market.symbol)}
                </div>
                <div className={`text-xs flex items-center justify-end gap-1 ${
                  isPositive ? 'text-green-400' : 'text-red-400'
                }`}>
                  <FontAwesomeIcon 
                    icon={isPositive ? faArrowUp : faArrowDown} 
                    className="text-[8px]" 
                  />
                  <span>{Math.abs(change).toFixed(2)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-800 bg-gray-900/30 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <FontAwesomeIcon icon={faBolt} className="text-yellow-500" />
          <span>Decibel API</span>
        </div>
        <span>Real-time prices</span>
      </div>
    </div>
  );
}
