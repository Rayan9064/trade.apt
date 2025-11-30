'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

// Decibel Market Data Types
export interface DecibelMarket {
  symbol: string;
  market_name: string;
  market_addr: string;
  max_leverage: number;
  tick_size: number;
  px_decimals: number;
  sz_decimals: number;
}

export interface DecibelPrice {
  market: string;
  symbol: string;
  mark_px: number;
  mid_px: number;
  oracle_px: number;
  funding_rate_bps: number;
  is_funding_positive: boolean;
  open_interest: number;
  timestamp_ms: number;
}

export interface DecibelCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface DecibelContextType {
  markets: DecibelMarket[];
  prices: Record<string, DecibelPrice>;
  isLoading: boolean;
  error: string | null;
  lastUpdate: Date | null;
  fetchMarkets: () => Promise<void>;
  fetchPrices: () => Promise<void>;
  fetchCandlesticks: (symbol: string, interval?: string, days?: number) => Promise<DecibelCandle[]>;
  getPrice: (symbol: string) => DecibelPrice | null;
  getMarket: (symbol: string) => DecibelMarket | null;
  availableSymbols: string[];
}

const DecibelContext = createContext<DecibelContextType | null>(null);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function DecibelProvider({ children }: { children: ReactNode }) {
  const [markets, setMarkets] = useState<DecibelMarket[]>([]);
  const [prices, setPrices] = useState<Record<string, DecibelPrice>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchMarkets = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/decibel/markets`);
      if (!response.ok) throw new Error('Failed to fetch markets');
      const data = await response.json();
      setMarkets(data.markets || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching Decibel markets:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch markets');
    }
  }, []);

  const fetchPrices = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/decibel/prices`);
      if (!response.ok) throw new Error('Failed to fetch prices');
      const data = await response.json();
      
      const priceMap: Record<string, DecibelPrice> = {};
      (data.prices || []).forEach((p: DecibelPrice) => {
        priceMap[p.symbol] = p;
      });
      
      setPrices(priceMap);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching Decibel prices:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch prices');
    }
  }, []);

  const fetchCandlesticks = useCallback(async (
    symbol: string, 
    interval: string = '1h', 
    days: number = 7
  ): Promise<DecibelCandle[]> => {
    try {
      const response = await fetch(
        `${API_URL}/decibel/candlesticks/${symbol}?interval=${interval}&days=${days}`
      );
      if (!response.ok) throw new Error(`Failed to fetch candlesticks for ${symbol}`);
      const data = await response.json();
      return data.candles || [];
    } catch (err) {
      console.error(`Error fetching candlesticks for ${symbol}:`, err);
      return [];
    }
  }, []);

  const getPrice = useCallback((symbol: string): DecibelPrice | null => {
    return prices[symbol.toUpperCase()] || null;
  }, [prices]);

  const getMarket = useCallback((symbol: string): DecibelMarket | null => {
    return markets.find(m => m.symbol.toUpperCase() === symbol.toUpperCase()) || null;
  }, [markets]);

  const availableSymbols = markets.map(m => m.symbol);

  // Initial fetch
  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await Promise.all([fetchMarkets(), fetchPrices()]);
      setIsLoading(false);
    };
    init();
  }, [fetchMarkets, fetchPrices]);

  // Auto-refresh prices every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchPrices();
    }, 10000);
    return () => clearInterval(interval);
  }, [fetchPrices]);

  return (
    <DecibelContext.Provider value={{
      markets,
      prices,
      isLoading,
      error,
      lastUpdate,
      fetchMarkets,
      fetchPrices,
      fetchCandlesticks,
      getPrice,
      getMarket,
      availableSymbols,
    }}>
      {children}
    </DecibelContext.Provider>
  );
}

export function useDecibel() {
  const context = useContext(DecibelContext);
  if (!context) {
    throw new Error('useDecibel must be used within a DecibelProvider');
  }
  return context;
}
