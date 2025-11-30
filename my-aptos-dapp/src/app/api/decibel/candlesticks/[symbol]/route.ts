/**
 * Decibel Candlesticks API Route
 * GET /api/decibel/candlesticks/[symbol] - Get OHLC chart data
 */

import { NextRequest, NextResponse } from 'next/server';

const DECIBEL_BASE_URL = 'https://api.netna.aptoslabs.com/decibel';
const DECIBEL_API_WALLET = process.env.DECIBEL_API_WALLET;

export interface DecibelCandle {
  timestamp: number;
  close_timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  interval: string;
}

// Cache for market addresses
let marketsCache: Record<string, string> = {};
let marketsCacheTime: number = 0;
const MARKETS_CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

async function getMarketAddress(symbol: string): Promise<string | null> {
  // Check cache
  if (Object.keys(marketsCache).length > 0 && Date.now() - marketsCacheTime < MARKETS_CACHE_DURATION) {
    return marketsCache[symbol.toUpperCase()] || null;
  }

  try {
    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/markets`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DECIBEL_API_WALLET}`,
      },
    });
    if (!response.ok) return null;
    
    const markets = await response.json();
    marketsCache = {};
    
    for (const market of markets) {
      const sym = (market.market_name || '').split('-')[0];
      if (market.market_addr && sym) {
        marketsCache[sym.toUpperCase()] = market.market_addr;
      }
    }
    marketsCacheTime = Date.now();
    
    return marketsCache[symbol.toUpperCase()] || null;
  } catch (error) {
    console.error('Error fetching markets:', error);
    return null;
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { symbol: string } }
) {
  try {
    const symbol = params.symbol.toUpperCase();
    const searchParams = request.nextUrl.searchParams;
    const interval = searchParams.get('interval') || '1h';
    const days = parseInt(searchParams.get('days') || '7', 10);

    // Get market address for symbol
    const marketAddr = await getMarketAddress(symbol);
    
    if (!marketAddr) {
      return NextResponse.json(
        { error: `Market not found for symbol: ${symbol}` },
        { status: 404 }
      );
    }

    // Calculate time range
    const endTime = Date.now();
    const startTime = endTime - (days * 24 * 60 * 60 * 1000);

    const response = await fetch(
      `${DECIBEL_BASE_URL}/api/v1/candlesticks?market=${marketAddr}&interval=${interval}&startTime=${startTime}&endTime=${endTime}`,
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${DECIBEL_API_WALLET}`,
        },
        cache: 'no-store'
      }
    );

    if (!response.ok) {
      console.error(`Decibel candlesticks API error: ${response.status}`);
      return NextResponse.json(
        { error: 'Failed to fetch candlesticks', status: response.status },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Transform the data
    const candles: DecibelCandle[] = data.map((candle: any) => ({
      timestamp: candle.t || 0,
      close_timestamp: candle.T || 0,
      open: candle.o || 0,
      high: candle.h || 0,
      low: candle.l || 0,
      close: candle.c || 0,
      volume: candle.v || 0,
      interval: candle.i || interval,
    }));

    // Sort by timestamp
    candles.sort((a, b) => a.timestamp - b.timestamp);

    // Calculate stats
    let stats = null;
    if (candles.length > 0) {
      const priceValues = candles.map(c => c.close);
      const currentPrice = priceValues[priceValues.length - 1];
      const startPrice = priceValues[0];
      const highPrice = Math.max(...candles.map(c => c.high));
      const lowPrice = Math.min(...candles.map(c => c.low));
      const priceChange = currentPrice - startPrice;
      const priceChangePercent = startPrice ? (priceChange / startPrice) * 100 : 0;

      stats = {
        current: currentPrice,
        open: startPrice,
        high: highPrice,
        low: lowPrice,
        change: priceChange,
        change_percent: Math.round(priceChangePercent * 100) / 100,
        period: `${days}d`
      };
    }

    // Format for frontend
    const prices = candles.map(c => ({ time: c.timestamp, value: c.close }));
    const ohlcv = candles.map(c => ({
      time: c.timestamp,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: c.volume
    }));

    return NextResponse.json({
      symbol,
      prices,
      ohlcv,
      stats,
      days,
      interval,
      data_points: candles.length,
      source: 'decibel',
      last_updated: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching candlesticks:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
