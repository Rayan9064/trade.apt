/**
 * Decibel Prices API Route
 * GET /api/decibel/prices - Get current prices from Decibel
 */

import { NextResponse } from 'next/server';

const DECIBEL_BASE_URL = 'https://api.netna.aptoslabs.com/decibel';
const DECIBEL_API_KEY = process.env.DECIBEL_API_KEY || '';

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

// Simple in-memory cache
let pricesCache: DecibelPrice[] | null = null;
let pricesCacheTime: number = 0;
const CACHE_DURATION = 5000; // 5 seconds for prices

// Market address to symbol mapping (populated from markets endpoint)
let marketAddrToSymbol: Record<string, string> = {};

async function loadMarketMappings() {
  try {
    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/markets`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DECIBEL_API_KEY}`,
      }
    });
    if (response.ok) {
      const markets = await response.json();
      marketAddrToSymbol = {};
      for (const market of markets) {
        const symbol = (market.market_name || '').split('-')[0];
        if (market.market_addr && symbol) {
          marketAddrToSymbol[market.market_addr] = symbol;
        }
      }
    }
  } catch (error) {
    console.error('Error loading market mappings:', error);
  }
}

export async function GET() {
  try {
    // Check cache
    if (pricesCache && Date.now() - pricesCacheTime < CACHE_DURATION) {
      return NextResponse.json(pricesCache);
    }

    // Ensure we have market mappings
    if (Object.keys(marketAddrToSymbol).length === 0) {
      await loadMarketMappings();
    }

    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/prices`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DECIBEL_API_KEY}`,
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      console.error(`Decibel prices API error: ${response.status}`);
      return NextResponse.json(
        { error: 'Failed to fetch prices', status: response.status },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Transform the data
    const prices: DecibelPrice[] = data.map((price: any) => ({
      market: price.market || '',
      symbol: marketAddrToSymbol[price.market] || 'UNKNOWN',
      mark_px: price.mark_px || 0,
      mid_px: price.mid_px || 0,
      oracle_px: price.oracle_px || 0,
      funding_rate_bps: price.funding_rate_bps || 0,
      is_funding_positive: price.is_funding_positive ?? true,
      open_interest: price.open_interest || 0,
      timestamp_ms: price.transaction_unix_ms || Date.now(),
    }));

    // Update cache
    pricesCache = prices;
    pricesCacheTime = Date.now();

    return NextResponse.json(prices);
  } catch (error) {
    console.error('Error fetching Decibel prices:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
