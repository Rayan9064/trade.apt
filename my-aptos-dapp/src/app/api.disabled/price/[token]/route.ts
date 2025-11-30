/**
 * Price API Route
 * GET /api/price/[token] - Get current price for a token
 */

import { NextRequest, NextResponse } from 'next/server';

const DECIBEL_BASE_URL = 'https://api.netna.aptoslabs.com/decibel';

// Cache
let marketsCache: Record<string, string> = {};
let marketsCacheTime: number = 0;
let pricesCache: Record<string, any> = {};
let pricesCacheTime: number = 0;
const MARKETS_CACHE_DURATION = 30 * 60 * 1000;
const PRICES_CACHE_DURATION = 5000; // 5 seconds

async function loadMarkets() {
  if (Object.keys(marketsCache).length > 0 && Date.now() - marketsCacheTime < MARKETS_CACHE_DURATION) {
    return;
  }

  try {
    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/markets`);
    if (response.ok) {
      const markets = await response.json();
      marketsCache = {};
      for (const market of markets) {
        const sym = (market.market_name || '').split('-')[0];
        if (market.market_addr && sym) {
          marketsCache[sym.toUpperCase()] = market.market_addr;
        }
      }
      marketsCacheTime = Date.now();
    }
  } catch {
    // Ignore
  }
}

async function loadPrices() {
  if (Object.keys(pricesCache).length > 0 && Date.now() - pricesCacheTime < PRICES_CACHE_DURATION) {
    return;
  }

  await loadMarkets();
  const addrToSymbol: Record<string, string> = {};
  for (const [sym, addr] of Object.entries(marketsCache)) {
    addrToSymbol[addr] = sym;
  }

  try {
    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/prices`, {
      cache: 'no-store'
    });
    if (response.ok) {
      const prices = await response.json();
      pricesCache = {};
      for (const price of prices) {
        const symbol = addrToSymbol[price.market];
        if (symbol) {
          pricesCache[symbol] = {
            symbol,
            price: price.oracle_px || price.mark_px || 0,
            mark_price: price.mark_px || 0,
            oracle_price: price.oracle_px || 0,
            funding_rate_bps: price.funding_rate_bps || 0,
            open_interest: price.open_interest || 0,
            timestamp: price.transaction_unix_ms || Date.now()
          };
        }
      }
      pricesCacheTime = Date.now();
    }
  } catch {
    // Ignore
  }
}

export async function GET(
  _request: NextRequest,
  { params }: { params: { token: string } }
) {
  try {
    const token = params.token.toUpperCase();

    // Handle stablecoins
    if (token === 'USDC' || token === 'USDT') {
      return NextResponse.json({
        symbol: token,
        price: 1.0,
        source: 'fixed'
      });
    }

    await loadPrices();

    const priceData = pricesCache[token];
    
    if (!priceData) {
      return NextResponse.json(
        { error: `Price not found for token: ${token}` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      ...priceData,
      source: 'decibel'
    });
  } catch (error) {
    console.error('Error fetching price:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
