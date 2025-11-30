'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';

export interface PriceData {
  symbol: string;
  price: number;
  change_24h: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
  last_update: string;
  source: string;
  is_stale: boolean;
}

export interface LivePrices {
  [symbol: string]: PriceData;
}

interface PriceContextType {
  prices: LivePrices;
  isConnected: boolean;
  lastUpdate: Date | null;
  getPrice: (symbol: string) => number | null;
  getFormattedPrice: (symbol: string) => string;
  getPriceChange: (symbol: string) => number;
  getPriceData: (symbol: string) => PriceData | null;
}

const PriceContext = createContext<PriceContextType | null>(null);

export function PriceProvider({ children }: { children: ReactNode }) {
  const [prices, setPrices] = useState<LivePrices>({});
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    try {
      const eventSource = new EventSource('/api/prices/stream');
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('🔌 Connected to live price stream');
        setIsConnected(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'initial' && data.prices) {
            setPrices(data.prices);
            setLastUpdate(new Date());
          } else if (data.type === 'update' && data.symbol && data.price) {
            setPrices((prev: LivePrices) => ({
              ...prev,
              [data.symbol]: data.price,
            }));
            setLastUpdate(new Date());
          }
        } catch (e) {
          console.error('Failed to parse price update:', e);
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        eventSource.close();
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    } catch (e) {
      console.error('Failed to connect:', e);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connect]);

  const getPrice = useCallback((symbol: string): number | null => {
    const data = prices[symbol.toUpperCase()];
    return data ? data.price : null;
  }, [prices]);

  const getFormattedPrice = useCallback((symbol: string): string => {
    const price = getPrice(symbol);
    if (price === null) return '---';
    if (price < 0.01) return `$${price.toFixed(6)}`;
    if (price < 1) return `$${price.toFixed(4)}`;
    if (price < 1000) return `$${price.toFixed(2)}`;
    return `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  }, [getPrice]);

  const getPriceChange = useCallback((symbol: string): number => {
    const data = prices[symbol.toUpperCase()];
    return data ? data.change_24h : 0;
  }, [prices]);

  const getPriceData = useCallback((symbol: string): PriceData | null => {
    return prices[symbol.toUpperCase()] || null;
  }, [prices]);

  return (
    <PriceContext.Provider value={{
      prices,
      isConnected,
      lastUpdate,
      getPrice,
      getFormattedPrice,
      getPriceChange,
      getPriceData,
    }}>
      {children}
    </PriceContext.Provider>
  );
}

export function usePrices() {
  const context = useContext(PriceContext);
  if (!context) {
    throw new Error('usePrices must be used within a PriceProvider');
  }
  return context;
}
