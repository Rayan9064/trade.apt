/**
 * Decibel Markets API Route
 * GET /api/decibel/markets - Get all available markets from Decibel
 */

import { NextResponse } from 'next/server';

const DECIBEL_BASE_URL = 'https://api.netna.aptoslabs.com/decibel';
const DECIBEL_API_WALLET = process.env.DECIBEL_API_WALLET || '';

export interface DecibelMarket {
  market_addr: string;
  market_name: string;
  symbol: string;
  lot_size: number;
  min_size: number;
  tick_size: number;
  px_decimals: number;
  sz_decimals: number;
  max_leverage: number;
  max_open_interest: number;
}

// Cache markets for 30 minutes
let marketsCache: DecibelMarket[] | null = null;
let marketsCacheTime: number = 0;
const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

export async function GET() {
  try {
    // Check cache
    if (marketsCache && Date.now() - marketsCacheTime < CACHE_DURATION) {
      return NextResponse.json(marketsCache);
    }

    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/markets`, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Wallet': DECIBEL_API_WALLET,
      },
      next: { revalidate: 1800 } // Cache for 30 minutes
    });

    if (!response.ok) {
      console.error(`Decibel markets API error: ${response.status}`);
      return NextResponse.json(
        { error: 'Failed to fetch markets', status: response.status },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Transform and cache the data
    const markets: DecibelMarket[] = data.map((market: any) => {
      const marketName = market.market_name || '';
      const symbol = marketName.split('-')[0] || marketName;
      
      return {
        market_addr: market.market_addr || '',
        market_name: marketName,
        symbol,
        lot_size: market.lot_size || 0,
        min_size: market.min_size || 0,
        tick_size: market.tick_size || 0,
        px_decimals: market.px_decimals || 0,
        sz_decimals: market.sz_decimals || 0,
        max_leverage: market.max_leverage || 0,
        max_open_interest: market.max_open_interest || 0,
      };
    });

    // Update cache
    marketsCache = markets;
    marketsCacheTime = Date.now();

    return NextResponse.json(markets);
  } catch (error) {
    console.error('Error fetching Decibel markets:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
