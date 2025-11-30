'use client';

import { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRobot, faPaperPlane, faWallet, faShieldAlt, faCheckCircle, faTimesCircle, faCircle, faChartLine } from '@fortawesome/free-solid-svg-icons';
import { usePrices } from '@/context/PriceContext';

interface Message {
  type: 'bot' | 'user' | 'approval' | 'live-price';
  content: string;
  trade?: TradeData;
  priceSymbols?: string[]; // Tokens mentioned in this message for live updates
  timestamp?: number;
}

interface TradeData {
  intent: string;
  action: string;
  tokenFrom: string;
  tokenTo: string;
  amountUsd: number;
  priceAtRequest?: number; // Price when user made the request
  conditions: {
    type: string;
    operator: string | null;
    value: number | null;
  };
}

interface ChatbotProps {
  onOpenCharts?: (tokens: string[]) => void;
}

// Comprehensive list of tokens to detect
const DETECTABLE_TOKENS = [
  'BTC', 'ETH', 'SOL', 'APT', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT',
  'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'ALGO', 'VET', 'FIL',
  'NEAR', 'OP', 'ARB', 'INJ', 'SUI', 'SEI', 'TIA', 'PEPE', 'SHIB', 'BONK',
  'ETC', 'FTM', 'AAVE', 'CRV', 'MKR', 'COMP', 'SNX', 'LDO', 'RPL', 'GMX',
  'DYDX', '1INCH', 'SUSHI', 'BAL', 'YFI', 'ENS', 'APE', 'SAND', 'MANA',
  'AXS', 'GALA', 'IMX', 'RNDR', 'FET', 'AGIX', 'OCEAN', 'TRX', 'TON', 'HBAR',
];

// Helper to extract token symbols from text
function extractTokenSymbols(text: string): string[] {
  const found: string[] = [];
  const upper = text.toUpperCase();
  
  // Also detect full names
  const tokenNameMap: Record<string, string> = {
    'BITCOIN': 'BTC',
    'ETHEREUM': 'ETH',
    'SOLANA': 'SOL',
    'APTOS': 'APT',
    'BINANCE': 'BNB',
    'RIPPLE': 'XRP',
    'CARDANO': 'ADA',
    'DOGECOIN': 'DOGE',
    'AVALANCHE': 'AVAX',
    'POLKADOT': 'DOT',
    'POLYGON': 'MATIC',
    'CHAINLINK': 'LINK',
    'UNISWAP': 'UNI',
    'COSMOS': 'ATOM',
    'LITECOIN': 'LTC',
    'STELLAR': 'XLM',
    'ALGORAND': 'ALGO',
    'FILECOIN': 'FIL',
    'FANTOM': 'FTM',
    'AAVE': 'AAVE',
    'CURVE': 'CRV',
    'MAKER': 'MKR',
    'COMPOUND': 'COMP',
    'SYNTHETIX': 'SNX',
  };
  
  // Check for full names first
  for (const [name, symbol] of Object.entries(tokenNameMap)) {
    if (upper.includes(name) && !found.includes(symbol)) {
      found.push(symbol);
    }
  }
  
  // Check for symbols
  for (const token of DETECTABLE_TOKENS) {
    // Use word boundary matching to avoid false positives
    const regex = new RegExp(`\\b${token}\\b`, 'i');
    if (regex.test(text) && !found.includes(token)) {
      found.push(token);
    }
  }
  
  return found;
}

// Detect if user is asking about price/chart/analysis
function shouldOpenChart(text: string): boolean {
  const chartKeywords = [
    'price', 'chart', 'show me', 'what is', 'how much', 'worth',
    'analyze', 'analysis', 'trend', 'graph', 'history', 'compare',
    'buy', 'sell', 'trade', 'market', 'performance', 'look at'
  ];
  const lower = text.toLowerCase();
  return chartKeywords.some(kw => lower.includes(kw));
}

export default function Chatbot({ onOpenCharts }: ChatbotProps) {
  const { prices, isConnected: pricesConnected, getFormattedPrice, getPriceChange } = usePrices();
  
  const [messages, setMessages] = useState<Message[]>([
    {
      type: 'bot',
      content: '👋 Hey! I\'m your AI trading assistant with **LIVE** prices!\n\n🔒 **Your Security:**\n• I only *parse* your requests - I never access your wallet\n• All trades require YOUR approval in your wallet\n• Your private keys stay with YOU\n\n📊 **Live Prices** update in real-time!\n\nConnect your wallet to start trading, or ask me about prices!',
      priceSymbols: ['BTC', 'ETH', 'APT'],
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check for Petra wallet on mount
  useEffect(() => {
    checkWalletConnection();
  }, []);

  const checkWalletConnection = async () => {
    if (typeof window !== 'undefined' && (window as any).aptos) {
      try {
        const wallet = (window as any).aptos;
        if (wallet.isConnected) {
          const account = await wallet.account();
          setWalletAddress(account.address);
        }
      } catch (e) {
        console.log('Wallet not connected');
      }
    }
  };

  const connectWallet = async () => {
    if (typeof window !== 'undefined' && (window as any).aptos) {
      try {
        const wallet = (window as any).aptos;
        const response = await wallet.connect();
        setWalletAddress(response.address);
        setMessages(prev => [...prev, {
          type: 'bot',
          content: `✅ Wallet connected!\n\n**Address:** ${response.address.slice(0, 6)}...${response.address.slice(-4)}\n\n🔒 Remember: I can ONLY suggest trades. YOU approve every transaction in your wallet. I never have access to your funds.`
        }]);
      } catch (error: any) {
        setMessages(prev => [...prev, {
          type: 'bot',
          content: '❌ Wallet connection failed. Make sure you have Petra or Pontem wallet installed!'
        }]);
      }
    } else {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: '🦊 No Aptos wallet detected!\n\nPlease install:\n• Petra Wallet (petra.app)\n• Pontem Wallet (pontem.network)\n\nThen refresh this page.'
      }]);
    }
  };

  const handleApprove = async (trade: TradeData) => {
    if (!walletAddress) {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: '⚠️ Please connect your wallet first to approve trades.'
      }]);
      return;
    }

    setMessages(prev => [...prev, {
      type: 'bot',
      content: '🔐 Opening wallet for approval...\n\n**Check your wallet popup!**\n\nYou\'ll see the exact transaction details there. Only sign if everything looks correct.'
    }]);

    try {
      // In a real implementation, this would create and submit the transaction
      // The wallet popup shows EXACTLY what will happen - user has full control
      const wallet = (window as any).aptos;
      
      // Example: Building an Aptos transaction (would use actual DEX contract)
      // const payload = {
      //   type: "entry_function_payload",
      //   function: "0x1::coin::transfer",
      //   type_arguments: ["0x1::aptos_coin::AptosCoin"],
      //   arguments: [receiverAddress, amount]
      // };
      // const response = await wallet.signAndSubmitTransaction(payload);
      
      // Simulated delay for demo
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setMessages(prev => [...prev, {
        type: 'bot',
        content: `✅ **Trade Submitted!**\n\n📋 **Order:**\n• ${trade.action.toUpperCase()} ${trade.amountUsd > 0 ? '$' + trade.amountUsd : ''} ${trade.tokenTo || trade.tokenFrom}\n${trade.conditions.type === 'price_trigger' ? `• Trigger: When price ${trade.conditions.operator} $${trade.conditions.value}` : '• Execution: Immediate'}\n\n🔗 Transaction will appear in your wallet history.\n\n_Note: This is a demo. In production, this executes on Aptos mainnet via your wallet._`
      }]);
      
    } catch (error: any) {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: `❌ Transaction cancelled or failed.\n\nReason: ${error.message || 'User rejected the transaction'}\n\nNo funds were moved. Try again when ready!`
      }]);
    }
  };

  const handleReject = () => {
    setMessages(prev => [...prev, {
      type: 'bot',
      content: '🚫 Trade cancelled. No transaction was created.\n\nLet me know if you\'d like to try something else!'
    }]);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    const mentionedTokens = extractTokenSymbols(userMessage);
    const userWantsChart = shouldOpenChart(userMessage);
    
    setInput('');
    setMessages((prev: Message[]) => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userMessage }),
      });

      const data = await response.json();

      if (data.success) {
        let botResponse = data.message || 'I understood your request.';
        
        // Add warnings if any
        if (data.warnings && data.warnings.length > 0) {
          botResponse += '\n\n' + data.warnings.map((w: string) => `⚠️ ${w}`).join('\n');
        }
        
        // Add suggestions if any
        if (data.suggestions && data.suggestions.length > 0) {
          botResponse += '\n\n💡 **Suggestions:**\n' + data.suggestions.map((s: string) => `• ${s}`).join('\n');
        }
        
        // Extract tokens mentioned in response for live price updates
        const responseTokens = extractTokenSymbols(botResponse);
        const allTokens = Array.from(new Set([...mentionedTokens, ...responseTokens]));
        
        // Open charts if user asked about tokens and mentioned price/chart keywords
        if (userWantsChart && allTokens.length > 0 && onOpenCharts) {
          onOpenCharts(allTokens);
        }
        
        // If there's an action that requires confirmation
        if (data.parsed && data.parsed.type && data.parsed.type !== 'none') {
          const action = data.parsed;
          
          // Get current live price for the trade token
          const tradeToken = action.token_to || action.token_from || 'APT';
          const currentPrice = prices[tradeToken]?.price || null;
          
          // Open chart for trade tokens
          const tradeTokens = [action.token_from, action.token_to].filter(Boolean);
          if (onOpenCharts && tradeTokens.length > 0) {
            onOpenCharts(tradeTokens);
          }
          
          // Add the conversational response with live prices
          setMessages((prev: Message[]) => [...prev, { 
            type: 'bot', 
            content: botResponse,
            priceSymbols: allTokens.length > 0 ? allTokens : undefined,
            timestamp: Date.now()
          }]);
          
          // Build trade object for approval with price at request time
          const trade: TradeData = {
            intent: data.intent || 'trade',
            action: action.type,
            tokenFrom: action.token_from || 'USDC',
            tokenTo: action.token_to || 'APT',
            amountUsd: action.amount_usd || 0,
            priceAtRequest: currentPrice ?? undefined, // Store price when user made request
            conditions: {
              type: action.condition?.type || 'immediate',
              operator: action.condition?.type === 'price_below' ? '<' : action.condition?.type === 'price_above' ? '>' : null,
              value: action.condition?.trigger_price || null
            }
          };
          
          // Only show approval if requires_confirmation
          if (action.requires_confirmation) {
            const riskEmoji = action.risk_level === 'high' ? '🔴' : action.risk_level === 'medium' ? '🟡' : '🟢';
            const approvalMsg = `🔐 **Trade Confirmation Required** ${riskEmoji}\n\n` +
              `• **Action:** ${trade.action.toUpperCase()}\n` +
              `• **From:** ${trade.tokenFrom}\n` +
              `• **To:** ${trade.tokenTo}\n` +
              `• **Amount:** ${trade.amountUsd > 0 ? '$' + trade.amountUsd.toLocaleString() : 'To be specified'}\n` +
              `• **Risk Level:** ${action.risk_level || 'low'}\n\n` +
              `⚠️ **Your wallet will prompt you to sign.**\nI prepare trades - YOU approve them.`;
            
            setMessages((prev: Message[]) => [...prev, { 
              type: 'approval', 
              content: approvalMsg,
              trade: trade
            }]);
          }
        } else {
          // Regular bot response with live price symbols
          setMessages((prev: Message[]) => [...prev, { 
            type: 'bot', 
            content: botResponse,
            priceSymbols: allTokens.length > 0 ? allTokens : undefined,
            timestamp: Date.now()
          }]);
        }
      } else {
        setMessages((prev: Message[]) => [...prev, { 
          type: 'bot', 
          content: data.message || data.error || 'Sorry, I couldn\'t process that. Try asking about crypto prices or making a trade!' 
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'bot', 
        content: 'Sorry, I\'m having trouble connecting. Make sure the server is running.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <aside className="panel-border border-r-0 border-t-0 border-b-0 bg-bg-panel flex flex-col h-full z-20">
      {/* Chat Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800 bg-gray-900/50">
        <div className="flex items-center">
          <div className="relative">
            <FontAwesomeIcon icon={faRobot} className="text-green-400 text-lg" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-bold text-white">AI ASSISTANT</h3>
            <p className="text-[10px] text-gray-500 flex items-center gap-1">
              <FontAwesomeIcon icon={faShieldAlt} className="text-green-500" />
              Read-only • You control trades
            </p>
          </div>
        </div>
        
        {/* Wallet Button */}
        <button
          onClick={connectWallet}
          className={`text-xs px-2 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
            walletAddress 
              ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
              : 'bg-aptos-blue/20 text-aptos-blue border border-aptos-blue/30 hover:bg-aptos-blue/30'
          }`}
        >
          <FontAwesomeIcon icon={faWallet} />
          {walletAddress ? `${walletAddress.slice(0, 4)}...${walletAddress.slice(-4)}` : 'Connect'}
        </button>
      </div>

      {/* Trust Banner with Live Status */}
      <div className="px-3 py-2 bg-green-500/10 border-b border-green-500/20 flex justify-between items-center">
        <p className="text-[10px] text-green-400 flex items-center gap-2">
          <FontAwesomeIcon icon={faShieldAlt} />
          AI parses only • Your keys stay with you
        </p>
        <div className="flex items-center gap-1.5">
          <FontAwesomeIcon 
            icon={faCircle} 
            className={`text-[6px] ${pricesConnected ? 'text-green-500 animate-pulse' : 'text-red-500'}`} 
          />
          <span className={`text-[10px] ${pricesConnected ? 'text-green-400' : 'text-red-400'}`}>
            {pricesConnected ? 'LIVE PRICES' : 'CONNECTING...'}
          </span>
        </div>
      </div>

      {/* Live Price Bar */}
      {pricesConnected && (
        <div className="px-3 py-1.5 bg-gray-900/50 border-b border-gray-800 flex gap-4 overflow-x-auto text-[10px]">
          {['BTC', 'ETH', 'SOL', 'APT'].map((symbol) => {
            const change = getPriceChange(symbol);
            const isPositive = change >= 0;
            return (
              <div key={symbol} className="flex items-center gap-1.5 shrink-0">
                <span className="text-gray-500">{symbol}</span>
                <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
                  {getFormattedPrice(symbol)}
                </span>
                <span className={`${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  {isPositive ? '↑' : '↓'}{Math.abs(change).toFixed(1)}%
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Chat History */}
      <div className="flex-grow p-4 overflow-y-auto space-y-4">
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'items-start'}`}>
            <div
              className={`p-3 rounded-lg text-xs leading-relaxed shadow-sm max-w-[90%] whitespace-pre-wrap ${
                message.type === 'user'
                  ? 'bg-aptos-blue text-white rounded-tr-none'
                  : message.type === 'approval'
                  ? 'bg-yellow-500/10 border border-yellow-500/30 text-gray-300 rounded-tl-none'
                  : 'bg-gray-800 border border-gray-700 text-gray-300 rounded-tl-none'
              }`}
            >
              {message.content}
              
              {/* Show live prices for tokens mentioned in message */}
              {message.type === 'bot' && message.priceSymbols && message.priceSymbols.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-700">
                  <div className="flex flex-wrap gap-2">
                    {message.priceSymbols.map((symbol) => {
                      const change = getPriceChange(symbol);
                      const isPositive = change >= 0;
                      return (
                        <div key={symbol} className="flex items-center gap-1 bg-gray-900 px-2 py-1 rounded">
                          <span className="text-gray-400">{symbol}:</span>
                          <span className={`font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                            {getFormattedPrice(symbol)}
                          </span>
                          <span className={`text-[10px] ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                            {isPositive ? '↑' : '↓'}{Math.abs(change).toFixed(2)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <p className="text-[9px] text-gray-600 mt-1">🔴 Live • Updates automatically</p>
                </div>
              )}
              
              {/* Approval Buttons with Live Price */}
              {message.type === 'approval' && message.trade && (
                <div className="mt-3">
                  {/* Show current live price vs requested price */}
                  <div className="mb-2 p-2 bg-gray-900 rounded text-[10px]">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Current {message.trade.tokenTo || message.trade.tokenFrom} Price:</span>
                      <span className="text-green-400 font-bold">
                        {getFormattedPrice(message.trade.tokenTo || message.trade.tokenFrom)}
                      </span>
                    </div>
                    {message.trade.priceAtRequest && (
                      <div className="flex justify-between mt-1">
                        <span className="text-gray-500">Price when requested:</span>
                        <span className="text-gray-400">${message.trade.priceAtRequest.toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(message.trade!)}
                      className="flex-1 bg-green-500 hover:bg-green-600 text-white py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition"
                    >
                      <FontAwesomeIcon icon={faCheckCircle} />
                      Approve & Sign
                    </button>
                    <button
                      onClick={handleReject}
                      className="flex-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition border border-red-500/30"
                    >
                      <FontAwesomeIcon icon={faTimesCircle} />
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-start">
            <div className="bg-gray-800 p-3 rounded-lg rounded-tl-none border border-gray-700 text-xs text-gray-300">
              <span className="animate-pulse">Analyzing request...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div className="p-4 border-t border-gray-800 bg-gray-900">
        <div className="relative">
          <input
            type="text"
            placeholder={walletAddress ? "Ask the AI agent..." : "Connect wallet or ask about prices..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            className="w-full bg-black border border-gray-700 text-gray-300 text-xs rounded-lg pl-3 pr-10 py-3 focus:outline-none focus:border-aptos-blue focus:ring-1 focus:ring-aptos-blue transition"
          />
          <button
            onClick={sendMessage}
            className="absolute right-2 top-2 text-aptos-blue hover:text-white p-1 rounded transition"
          >
            <FontAwesomeIcon icon={faPaperPlane} />
          </button>
        </div>
      </div>
    </aside>
  );
}
