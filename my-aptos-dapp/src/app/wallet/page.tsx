'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface WalletInfo {
  address: string;
  type: string;
  network: 'mainnet' | 'testnet' | 'devnet';
  balance: number;
  usd_value: number | null;
}

interface Transaction {
  hash: string;
  type: string;
  amount: number;
  timestamp: string;
}

export default function WalletPage() {
  const router = useRouter();
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFaucetLoading, setIsFaucetLoading] = useState(false);
  const [faucetMessage, setFaucetMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [network, setNetwork] = useState<'mainnet' | 'testnet' | 'devnet'>('testnet');

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('session_token');
      const address = localStorage.getItem('wallet_address');
      const storedNetwork = localStorage.getItem('network') as 'mainnet' | 'testnet' | 'devnet';
      const walletType = localStorage.getItem('wallet_type') || 'petra';

      if (!token || !address) {
        router.push('/login');
        return;
      }

      if (storedNetwork) {
        setNetwork(storedNetwork);
      }

      await loadBalance(address, storedNetwork || 'testnet', walletType);
    };

    checkAuth();
  }, [router]);

  const loadBalance = async (address: string, net: string, walletType: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/wallet/balance/${address}?network=${net}`);
      
      if (response.ok) {
        const data = await response.json();
        setWallet({
          address,
          type: walletType,
          network: net as 'mainnet' | 'testnet' | 'devnet',
          balance: data.apt_balance || 0,
          usd_value: data.usd_value,
        });
      } else {
        setWallet({
          address,
          type: walletType,
          network: net as 'mainnet' | 'testnet' | 'devnet',
          balance: 0,
          usd_value: null,
        });
      }
    } catch (error) {
      console.error('Failed to load balance:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNetworkChange = async (newNetwork: 'mainnet' | 'testnet' | 'devnet') => {
    setNetwork(newNetwork);
    localStorage.setItem('network', newNetwork);

    if (wallet) {
      setIsLoading(true);
      await loadBalance(wallet.address, newNetwork, wallet.type);
    }
  };

  const handleRequestFaucet = async () => {
    if (!wallet || network === 'mainnet') return;

    setIsFaucetLoading(true);
    setFaucetMessage(null);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/wallet/faucet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address: wallet.address,
          amount_apt: 1,
          network: network,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setFaucetMessage({ type: 'success', text: 'Successfully received 1 APT from faucet' });
        // Refresh balance after a delay
        setTimeout(async () => {
          await loadBalance(wallet.address, network, wallet.type);
        }, 2000);
      } else {
        setFaucetMessage({ type: 'error', text: data.error || 'Faucet request failed' });
      }
    } catch (error) {
      setFaucetMessage({ type: 'error', text: 'Network error - try again later' });
    } finally {
      setIsFaucetLoading(false);
    }
  };

  const handleDisconnect = async () => {
    const token = localStorage.getItem('session_token');
    
    if (token) {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    localStorage.removeItem('session_token');
    localStorage.removeItem('wallet_address');
    localStorage.removeItem('wallet_type');
    localStorage.removeItem('network');
    router.push('/login');
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 10)}...${address.slice(-8)}`;
  };

  const copyAddress = () => {
    if (wallet) {
      navigator.clipboard.writeText(wallet.address);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading wallet...</p>
        </div>
      </div>
    );
  }

  if (!wallet) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-xl font-bold text-white">Trade.apt</span>
          </Link>

          <Link
            href="/"
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Trading
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">Wallet Management</h1>

        {/* Wallet Card */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700 overflow-hidden mb-6">
          {/* Wallet Header */}
          <div className="p-6 border-b border-slate-700 bg-gradient-to-r from-purple-500/10 to-pink-500/10">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-2xl font-bold">
                {wallet.type[0].toUpperCase()}
              </div>
              <div>
                <p className="text-sm text-gray-400 capitalize">{wallet.type} Wallet</p>
                <div className="flex items-center gap-2">
                  <p className="text-xl text-white font-mono">{formatAddress(wallet.address)}</p>
                  <button
                    onClick={copyAddress}
                    className="p-1 hover:bg-slate-700 rounded transition-colors"
                    title="Copy address"
                  >
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Balance Section */}
          <div className="p-6 border-b border-slate-700">
            <p className="text-sm text-gray-400 mb-2">Current Balance</p>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-white">{wallet.balance.toFixed(4)}</span>
              <span className="text-xl text-gray-400">APT</span>
            </div>
            {wallet.usd_value !== null && (
              <p className="text-sm text-gray-400 mt-1">
                Approximately ${wallet.usd_value.toFixed(2)} USD
              </p>
            )}
          </div>

          {/* Network Selection */}
          <div className="p-6 border-b border-slate-700">
            <p className="text-sm text-gray-400 mb-3">Network</p>
            <div className="grid grid-cols-3 gap-3">
              {(['mainnet', 'testnet', 'devnet'] as const).map((net) => (
                <button
                  key={net}
                  onClick={() => handleNetworkChange(net)}
                  className={`py-3 px-4 rounded-xl text-sm font-medium transition-all ${
                    network === net
                      ? net === 'mainnet'
                        ? 'bg-green-500 text-white'
                        : net === 'testnet'
                        ? 'bg-yellow-500 text-black'
                        : 'bg-purple-500 text-white'
                      : 'bg-slate-700 text-gray-400 hover:bg-slate-600'
                  }`}
                >
                  {net.charAt(0).toUpperCase() + net.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Faucet Section (Testnet/Devnet only) */}
          {network !== 'mainnet' && (
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-sm text-gray-400">Testnet Faucet</p>
                  <p className="text-xs text-gray-500">Get free APT tokens for testing</p>
                </div>
                <button
                  onClick={handleRequestFaucet}
                  disabled={isFaucetLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors disabled:opacity-50"
                >
                  {isFaucetLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
                      <span>Requesting...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      <span>Request 1 APT</span>
                    </>
                  )}
                </button>
              </div>

              {faucetMessage && (
                <div className={`p-3 rounded-lg ${
                  faucetMessage.type === 'success' 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {faucetMessage.text}
                </div>
              )}

              <a
                href="https://aptoslabs.com/testnet-faucet"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 mt-3 text-sm text-purple-400 hover:text-purple-300"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Official Aptos Faucet
              </a>
            </div>
          )}

          {/* Quick Links */}
          <div className="p-6">
            <p className="text-sm text-gray-400 mb-3">Quick Links</p>
            <div className="space-y-2">
              <a
                href={`https://explorer.aptoslabs.com/account/${wallet.address}?network=${network}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <span className="text-white">View on Aptos Explorer</span>
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
              <a
                href="https://aptoslabs.com/developers"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <span className="text-white">Aptos Developer Docs</span>
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* Disconnect Button */}
        <button
          onClick={handleDisconnect}
          className="w-full flex items-center justify-center gap-2 py-4 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-xl transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Disconnect Wallet
        </button>

        {/* Aptos Info Card */}
        <div className="mt-8 bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Aptos Network Information</h2>
          
          <div className="space-y-4 text-sm text-gray-400">
            <div>
              <p className="text-white font-medium mb-1">Mainnet</p>
              <p>Production network with real value. Use for actual transactions.</p>
            </div>
            <div>
              <p className="text-white font-medium mb-1">Testnet</p>
              <p>Testing network that mirrors mainnet. Free tokens available from faucet. Perfect for testing trades.</p>
            </div>
            <div>
              <p className="text-white font-medium mb-1">Devnet</p>
              <p>Development network that resets frequently. Best for developers testing new features.</p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
            <p className="text-purple-400 text-sm">
              <strong>Tip:</strong> Start with Testnet to practice trading without risking real assets. 
              Use the faucet to get free APT tokens, then test the AI trading assistant to learn 
              how it works before moving to Mainnet.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
