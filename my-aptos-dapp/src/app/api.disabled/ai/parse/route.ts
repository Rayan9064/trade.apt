/**
 * AI Parse API Route
 * POST /api/ai/parse - Parse user intent for trading actions
 */

import { NextRequest, NextResponse } from 'next/server';

const GROQ_API_KEY = process.env.GROQ_API_KEY;
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';

const SYSTEM_PROMPT = `You are a trading intent parser for Trade.apt, an Aptos blockchain trading platform.

Your job is to analyze user messages and extract trading intents in a structured format.

For each message, determine:
1. Type: "buy", "sell", "swap", "price_check", "analysis", "alert", "none"
2. Token information (from/to)
3. Amount (in USD or token quantity)
4. Conditions (price triggers, etc.)
5. Risk level

ALWAYS respond in valid JSON format with this structure:
{
  "success": true,
  "intent": "description of what user wants",
  "message": "friendly response to user",
  "parsed": {
    "type": "buy|sell|swap|price_check|analysis|alert|none",
    "token_from": "USDC",
    "token_to": "BTC",
    "amount_usd": 100,
    "amount_tokens": null,
    "condition": {
      "type": "immediate|price_above|price_below",
      "trigger_price": null
    },
    "requires_confirmation": true,
    "risk_level": "low|medium|high"
  },
  "warnings": [],
  "suggestions": []
}

Examples:
- "Buy $100 of BTC" → type: "buy", token_to: "BTC", amount_usd: 100, requires_confirmation: true
- "What's the price of ETH?" → type: "price_check", token_to: "ETH", requires_confirmation: false
- "Sell all my SOL when it hits $200" → type: "sell", token_from: "SOL", condition: {type: "price_above", trigger_price: 200}

Keep responses friendly and include relevant trading warnings.`;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { text } = body;

    if (!text) {
      return NextResponse.json(
        { success: false, error: 'Text is required' },
        { status: 400 }
      );
    }

    if (!GROQ_API_KEY) {
      // Fallback parsing without AI
      return NextResponse.json(fallbackParse(text));
    }

    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GROQ_API_KEY}`
      },
      body: JSON.stringify({
        model: 'llama-3.1-70b-versatile',
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: text }
        ],
        temperature: 0.3,
        max_tokens: 1024,
        response_format: { type: "json_object" }
      })
    });

    if (!response.ok) {
      console.error('Groq API error:', await response.text());
      return NextResponse.json(fallbackParse(text));
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content;

    if (!content) {
      return NextResponse.json(fallbackParse(text));
    }

    try {
      const parsed = JSON.parse(content);
      return NextResponse.json(parsed);
    } catch {
      return NextResponse.json(fallbackParse(text));
    }
  } catch (error) {
    console.error('AI parse error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// Fallback parsing without AI
function fallbackParse(text: string) {
  const lower = text.toLowerCase();
  const tokens = ['BTC', 'ETH', 'SOL', 'APT', 'BNB', 'XRP', 'DOGE', 'AVAX'];
  
  // Find mentioned token
  let detectedToken: string | null = null;
  for (const token of tokens) {
    if (lower.includes(token.toLowerCase())) {
      detectedToken = token;
      break;
    }
  }

  // Detect intent
  const isBuy = /\b(buy|purchase|get|acquire)\b/i.test(text);
  const isSell = /\b(sell|dump|exit)\b/i.test(text);
  const isPrice = /\b(price|worth|cost|value|how much)\b/i.test(text);
  const isAnalysis = /\b(analyze|analysis|chart|trend|predict)\b/i.test(text);

  // Extract amount
  const amountMatch = text.match(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)/);
  const amount = amountMatch ? parseFloat(amountMatch[1].replace(',', '')) : null;

  if (isBuy && detectedToken) {
    return {
      success: true,
      intent: `Buy ${detectedToken}`,
      message: `I can help you buy ${detectedToken}${amount ? ` for $${amount}` : ''}. Please confirm the trade details.`,
      parsed: {
        type: 'buy',
        token_from: 'USDC',
        token_to: detectedToken,
        amount_usd: amount,
        condition: { type: 'immediate' },
        requires_confirmation: true,
        risk_level: 'medium'
      },
      warnings: ['Always verify the transaction in your wallet before signing.'],
      suggestions: [`Check the current ${detectedToken} price before buying.`]
    };
  }

  if (isSell && detectedToken) {
    return {
      success: true,
      intent: `Sell ${detectedToken}`,
      message: `I can help you sell ${detectedToken}. Please confirm the trade details.`,
      parsed: {
        type: 'sell',
        token_from: detectedToken,
        token_to: 'USDC',
        amount_usd: amount,
        condition: { type: 'immediate' },
        requires_confirmation: true,
        risk_level: 'medium'
      },
      warnings: ['Always verify the transaction in your wallet before signing.'],
      suggestions: []
    };
  }

  if (isPrice && detectedToken) {
    return {
      success: true,
      intent: `Price check for ${detectedToken}`,
      message: `Here's the current price information for ${detectedToken}. Check the live price ticker above!`,
      parsed: {
        type: 'price_check',
        token_to: detectedToken,
        requires_confirmation: false,
        risk_level: 'low'
      },
      warnings: [],
      suggestions: []
    };
  }

  if (isAnalysis && detectedToken) {
    return {
      success: true,
      intent: `Analysis for ${detectedToken}`,
      message: `I can show you chart analysis for ${detectedToken}. Check the chart panel for detailed price history and trends.`,
      parsed: {
        type: 'analysis',
        token_to: detectedToken,
        requires_confirmation: false,
        risk_level: 'low'
      },
      warnings: ['Past performance does not guarantee future results.'],
      suggestions: ['Compare with other assets for better insights.']
    };
  }

  // Default response
  return {
    success: true,
    intent: 'general',
    message: `I'm your AI trading assistant! I can help you:\n\n• Check crypto prices (e.g., "What's the price of BTC?")\n• Buy/sell tokens (e.g., "Buy $100 of ETH")\n• Analyze markets (e.g., "Analyze SOL trend")\n\nHow can I help you today?`,
    parsed: {
      type: 'none',
      requires_confirmation: false,
      risk_level: 'low'
    },
    warnings: [],
    suggestions: ['Try asking about BTC, ETH, SOL, or APT prices!']
  };
}
