/**
 * Chart API Route
 * GET /api/chart/[token] - Get chart data for a token
 */

import { NextRequest, NextResponse } from 'next/server';

const DECIBEL_BASE_URL = 'https://api.netna.aptoslabs.com/decibel';

// Cache for market addresses
let marketsCache: Record<string, string> = {};
let marketsCacheTime: number = 0;
const MARKETS_CACHE_DURATION = 30 * 60 * 1000;

// Chart data cache
const chartCache: Record<string, { data: any; time: number }> = {};
const CHART_CACHE_DURATION = 60 * 1000; // 1 minute

async function getMarketAddress(symbol: string): Promise<string | null> {
  if (Object.keys(marketsCache).length > 0 && Date.now() - marketsCacheTime < MARKETS_CACHE_DURATION) {
    return marketsCache[symbol.toUpperCase()] || null;
  }

  try {
    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/markets`);
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
  } catch {
    return null;
  }
}

function getIntervalForDays(days: number): string {
  if (days <= 1) return '15m';
  if (days <= 7) return '1h';
  if (days <= 30) return '4h';
  return '1d';
}

export async function GET(
  request: NextRequest,
  { params }: { params: { token: string } }
) {
  try {
    const token = params.token.toUpperCase();
    const searchParams = request.nextUrl.searchParams;
    const days = parseInt(searchParams.get('days') || '7', 10);
    const cacheKey = `${token}_${days}`;

    // Check cache
    const cached = chartCache[cacheKey];
    if (cached && Date.now() - cached.time < CHART_CACHE_DURATION) {
      return NextResponse.json(cached.data);
    }

    // Get market address
    const marketAddr = await getMarketAddress(token);
    
    if (!marketAddr) {
      return NextResponse.json(
        { error: `Market not found for token: ${token}` },
        { status: 404 }
      );
    }

    const interval = getIntervalForDays(days);
    const endTime = Date.now();
    const startTime = endTime - (days * 24 * 60 * 60 * 1000);

    const response = await fetch(
      `${DECIBEL_BASE_URL}/api/v1/candlesticks?market=${marketAddr}&interval=${interval}&startTime=${startTime}&endTime=${endTime}`,
      { cache: 'no-store' }
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch chart data' },
        { status: response.status }
      );
    }

    const candles = await response.json();
    
    // Sort and format
    candles.sort((a: any, b: any) => (a.t || 0) - (b.t || 0));

    const prices = candles.map((c: any) => ({ 
      time: c.t || 0, 
      value: c.c || 0 
    }));

    // Calculate stats
    let stats = null;
    if (candles.length > 0) {
      const priceValues = candles.map((c: any) => c.c || 0);
      const currentPrice = priceValues[priceValues.length - 1];
      const startPrice = priceValues[0];
      const highPrice = Math.max(...candles.map((c: any) => c.h || 0));
      const lowPrice = Math.min(...candles.map((c: any) => c.l || 0));
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

    const result = {
      symbol: token,
      prices,
      stats,
      days,
      interval,
      data_points: prices.length,
      source: 'decibel',
      last_updated: new Date().toISOString()
    };

    // Cache the result
    chartCache[cacheKey] = { data: result, time: Date.now() };

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error fetching chart data:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
