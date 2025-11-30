'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface WalletInfo {
  name: string;
  icon: string;
  installed: boolean;
  connect: () => Promise<string | null>;
}

export default function LoginPage() {
  const router = useRouter();
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wallets, setWallets] = useState<WalletInfo[]>([]);
  const [network, setNetwork] = useState<'mainnet' | 'testnet' | 'devnet'>('testnet');

  useEffect(() => {
    // Check for installed wallets
    const checkWallets = () => {
      const petraInstalled = typeof window !== 'undefined' && 'aptos' in window;
      const pontemInstalled = typeof window !== 'undefined' && 'pontem' in window;
      const martianInstalled = typeof window !== 'undefined' && 'martian' in window;

      setWallets([
        {
          name: 'Petra',
          icon: '/petra.svg',
          installed: petraInstalled,
          connect: async () => {
            try {
              const w = window as any;
              if (w.aptos) {
                const response = await w.aptos.connect();
                return response.address;
              }
              return null;
            } catch (e) {
              console.error('Petra connection error:', e);
              return null;
            }
          },
        },
        {
          name: 'Pontem',
          icon: '/pontem.svg',
          installed: pontemInstalled,
          connect: async () => {
            try {
              const w = window as any;
              if (w.pontem) {
                const response = await w.pontem.connect();
                return response.address;
              }
              return null;
            } catch (e) {
              console.error('Pontem connection error:', e);
              return null;
            }
          },
        },
        {
          name: 'Martian',
          icon: '/martian.svg',
          installed: martianInstalled,
          connect: async () => {
            try {
              const w = window as any;
              if (w.martian) {
                const response = await w.martian.connect();
                return response.address;
              }
              return null;
            } catch (e) {
              console.error('Martian connection error:', e);
              return null;
            }
          },
        },
      ]);
    };

    checkWallets();
    
    // Re-check after a short delay (wallets may inject late)
    const timeout = setTimeout(checkWallets, 500);
    return () => clearTimeout(timeout);
  }, []);

  const handleConnect = async (wallet: WalletInfo) => {
    if (!wallet.installed) {
      // Open wallet download page
      const urls: Record<string, string> = {
        'Petra': 'https://petra.app',
        'Pontem': 'https://pontem.network',
        'Martian': 'https://martianwallet.xyz',
      };
      window.open(urls[wallet.name], '_blank');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const address = await wallet.connect();
      
      if (!address) {
        setError('Failed to get wallet address');
        setIsConnecting(false);
        return;
      }

      // Login to backend
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallet_address: address,
          wallet_type: wallet.name.toLowerCase(),
          network: network,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        localStorage.setItem('session_token', data.session_token);
        localStorage.setItem('network', network);
        localStorage.setItem('wallet_address', address);
        localStorage.setItem('wallet_type', wallet.name.toLowerCase());
        router.push('/');
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (e) {
      console.error('Connection error:', e);
      setError('Connection failed. Please try again.');
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 mb-4">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Trade.apt</h1>
          <p className="text-gray-400">AI-Powered DeFi Trading Assistant</p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700 p-6">
          <h2 className="text-xl font-semibold text-white mb-6 text-center">Connect Your Wallet</h2>

          {/* Network Selection */}
          <div className="mb-6">
            <label className="block text-sm text-gray-400 mb-2">Select Network</label>
            <div className="grid grid-cols-3 gap-2">
              {(['mainnet', 'testnet', 'devnet'] as const).map((net) => (
                <button
                  key={net}
                  onClick={() => setNetwork(net)}
                  className={`py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    network === net
                      ? 'bg-purple-500 text-white'
                      : 'bg-slate-700 text-gray-400 hover:bg-slate-600'
                  }`}
                >
                  {net.charAt(0).toUpperCase() + net.slice(1)}
                </button>
              ))}
            </div>
            {network !== 'mainnet' && (
              <p className="text-xs text-green-400 mt-2">
                Using {network} - You can request free APT from the faucet
              </p>
            )}
          </div>

          {/* Wallet Options */}
          <div className="space-y-3">
            {wallets.map((wallet) => (
              <button
                key={wallet.name}
                onClick={() => handleConnect(wallet)}
                disabled={isConnecting}
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-all ${
                  wallet.installed
                    ? 'bg-slate-700 hover:bg-slate-600 border border-slate-600'
                    : 'bg-slate-800 border border-slate-700 opacity-70'
                } ${isConnecting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-slate-600 flex items-center justify-center text-lg font-bold text-white">
                    {wallet.name[0]}
                  </div>
                  <div className="text-left">
                    <p className="text-white font-medium">{wallet.name}</p>
                    <p className="text-xs text-gray-400">
                      {wallet.installed ? 'Detected' : 'Not installed'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {wallet.installed ? (
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                      Ready
                    </span>
                  ) : (
                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                      Install
                    </span>
                  )}
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {isConnecting && (
            <div className="mt-4 flex items-center justify-center gap-2 text-purple-400">
              <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span className="text-sm">Connecting...</span>
            </div>
          )}

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-xs text-gray-500">New to Aptos?</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>

          {/* Helpful Links */}
          <div className="space-y-2">
            <a
              href="https://petra.app"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-purple-400 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              Get Petra Wallet (Recommended)
            </a>
            <a
              href="https://aptoslabs.com/testnet-faucet"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-purple-400 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              Aptos Testnet Faucet
            </a>
            <a
              href="https://explorer.aptoslabs.com/?network=testnet"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-purple-400 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              Aptos Explorer
            </a>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-500 mt-6">
          By connecting, you agree to our terms of service
        </p>
      </div>
    </div>
  );
}
