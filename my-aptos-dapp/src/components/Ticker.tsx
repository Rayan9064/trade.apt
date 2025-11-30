'use client';

export default function Ticker() {
  const tickerItems = [
    { symbol: 'BTC', price: '$68,500', change: '▲ 1.4%', positive: true },
    { symbol: 'SOL', price: '$145.00', change: '▼ 2.5%', positive: false },
    { symbol: 'ETH', price: '$3,450', change: '▲ 1.2%', positive: true },
    { symbol: 'APT', price: '$14.20', change: '▬ 0.0%', positive: null },
    { symbol: 'DOGE', price: '$0.1500', change: '▼ 4.1%', positive: false },
  ];

  return (
    <div className="h-10 bg-gray-900 border-b border-gray-800 flex items-center shrink-0">
      <div className="px-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-r border-gray-800 h-full flex items-center bg-gray-900 z-10">
        Market Ticker
      </div>
      <div className="ticker-wrap text-xs font-mono">
        <div className="ticker-content py-2">
          {tickerItems.map((item, index) => (
            <span
              key={index}
              className={`mx-4 ${
                item.positive === true
                  ? 'text-green-400'
                  : item.positive === false
                  ? 'text-danger'
                  : 'text-aptos-blue'
              }`}
            >
              {item.symbol} {item.price} {item.change}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
