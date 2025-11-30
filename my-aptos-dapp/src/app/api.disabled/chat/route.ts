/**
 * AI Chat API Route
 * POST /api/chat - AI trading assistant powered by Groq
 */

import { NextRequest, NextResponse } from 'next/server';

const GROQ_API_KEY = process.env.GROQ_API_KEY;
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';

const SYSTEM_PROMPT = `You are Trade.apt AI, a helpful cryptocurrency trading assistant for the Aptos blockchain ecosystem.

You help users with:
1. Understanding crypto markets and trading concepts
2. Analyzing price movements and market trends
3. Explaining DeFi concepts and Aptos ecosystem
4. Providing trading insights (NOT financial advice)
5. Answering questions about Trade.apt platform features

Important guidelines:
- Always clarify you're NOT providing financial advice
- Be helpful but cautious about specific price predictions
- Explain technical concepts in simple terms
- If asked about specific trades, provide educational context
- Stay focused on crypto trading and Aptos ecosystem topics

Current platform features:
- Real-time price data from Decibel.trade (Aptos perpetuals)
- Price charts and market analysis
- Wallet integration for Aptos
- Price alerts and notifications`;

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, history = [] } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    if (!GROQ_API_KEY) {
      // Fallback response if no API key
      return NextResponse.json({
        response: "I'm Trade.apt AI assistant. Currently, my advanced AI features are being configured. In the meantime, I can help you navigate the platform. You can view real-time prices, charts, and connect your Aptos wallet to start trading!",
        source: 'fallback'
      });
    }

    // Build messages array
    const messages: ChatMessage[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...history.slice(-10), // Keep last 10 messages for context
      { role: 'user', content: message }
    ];

    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GROQ_API_KEY}`
      },
      body: JSON.stringify({
        model: 'llama-3.1-70b-versatile',
        messages,
        temperature: 0.7,
        max_tokens: 1024,
        top_p: 0.9
      })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Groq API error:', error);
      return NextResponse.json(
        { error: 'AI service unavailable' },
        { status: 503 }
      );
    }

    const data = await response.json();
    const aiResponse = data.choices?.[0]?.message?.content || 'I apologize, but I could not generate a response.';

    return NextResponse.json({
      response: aiResponse,
      source: 'groq',
      model: 'llama-3.1-70b-versatile'
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
