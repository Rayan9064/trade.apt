/**
 * Prices Stream API Route
 * GET /api/prices/stream - Server-Sent Events for real-time prices
 */

import { NextRequest } from 'next/server';

const DECIBEL_BASE_URL = 'https://api.netna.aptoslabs.com/decibel';

// Cache
let marketsCache: Record<string, string> = {};
let addrToSymbol: Record<string, string> = {};
let marketsCacheTime: number = 0;
const MARKETS_CACHE_DURATION = 30 * 60 * 1000;

async function loadMarkets() {
  if (Object.keys(marketsCache).length > 0 && Date.now() - marketsCacheTime < MARKETS_CACHE_DURATION) {
    return;
  }

  try {
    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/markets`);
    if (response.ok) {
      const markets = await response.json();
      marketsCache = {};
      addrToSymbol = {};
      for (const market of markets) {
        const sym = (market.market_name || '').split('-')[0];
        if (market.market_addr && sym) {
          marketsCache[sym.toUpperCase()] = market.market_addr;
          addrToSymbol[market.market_addr] = sym.toUpperCase();
        }
      }
      marketsCacheTime = Date.now();
    }
  } catch {
    // Ignore
  }
}

async function fetchPrices(): Promise<Record<string, any>> {
  await loadMarkets();

  try {
    const response = await fetch(`${DECIBEL_BASE_URL}/api/v1/prices`, {
      cache: 'no-store'
    });
    if (!response.ok) return {};

    const prices = await response.json();
    const result: Record<string, any> = {};

    for (const price of prices) {
      const symbol = addrToSymbol[price.market];
      if (symbol) {
        result[symbol] = {
          symbol,
          price: price.oracle_px || price.mark_px || 0,
          change_24h: 0, // Decibel doesn't provide this directly
          high_24h: 0,
          low_24h: 0,
          volume_24h: 0,
          funding_rate: price.funding_rate_bps || 0,
          open_interest: price.open_interest || 0,
          last_update: new Date().toISOString(),
          source: 'decibel'
        };
      }
    }

    // Add stablecoins
    result['USDC'] = { symbol: 'USDC', price: 1.0, source: 'fixed' };
    result['USDT'] = { symbol: 'USDT', price: 1.0, source: 'fixed' };

    return result;
  } catch {
    return {};
  }
}

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      // Send initial prices
      try {
        const prices = await fetchPrices();
        const initMessage = `data: ${JSON.stringify({ type: 'init', prices })}\n\n`;
        controller.enqueue(encoder.encode(initMessage));
      } catch (error) {
        console.error('Error fetching initial prices:', error);
      }

      // Set up interval to send price updates
      const intervalId = setInterval(async () => {
        try {
          const prices = await fetchPrices();
          const updateMessage = `data: ${JSON.stringify({ type: 'update', prices })}\n\n`;
          controller.enqueue(encoder.encode(updateMessage));
        } catch (error) {
          console.error('Error in price update:', error);
        }
      }, 5000); // Update every 5 seconds

      // Send heartbeat every 30 seconds
      const heartbeatId = setInterval(() => {
        try {
          const heartbeat = `data: ${JSON.stringify({ type: 'heartbeat', timestamp: new Date().toISOString() })}\n\n`;
          controller.enqueue(encoder.encode(heartbeat));
        } catch {
          // Ignore heartbeat errors
        }
      }, 30000);

      // Handle client disconnect
      request.signal.addEventListener('abort', () => {
        clearInterval(intervalId);
        clearInterval(heartbeatId);
        controller.close();
      });
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
