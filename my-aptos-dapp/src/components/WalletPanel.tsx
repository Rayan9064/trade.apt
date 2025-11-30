'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface WalletInfo {
  address: string;
  type: string;
  network: 'mainnet' | 'testnet' | 'devnet';
  balance: number;
}

export default function WalletPanel() {
  const router = useRouter();
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFaucetLoading, setIsFaucetLoading] = useState(false);
  const [faucetMessage, setFaucetMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    const loadWallet = async () => {
      const token = localStorage.getItem('session_token');
      const address = localStorage.getItem('wallet_address');
      const network = (localStorage.getItem('network') || 'testnet') as 'mainnet' | 'testnet' | 'devnet';
      const walletType = localStorage.getItem('wallet_type') || 'petra';

      if (!token || !address) {
        setIsLoading(false);
        return;
      }

      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_URL}/wallet/balance/${address}?network=${network}`);
        
        if (response.ok) {
          const data = await response.json();
          setWallet({
            address,
            type: walletType,
            network,
            balance: data.apt_balance || 0,
          });
        } else {
          setWallet({
            address,
            type: walletType,
            network,
            balance: 0,
          });
        }
      } catch (error) {
        console.error('Failed to load wallet:', error);
        setWallet({
          address,
          type: walletType,
          network,
          balance: 0,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadWallet();
  }, []);

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
    setWallet(null);
    router.push('/login');
  };

  const handleRequestFaucet = async () => {
    if (!wallet || wallet.network === 'mainnet') return;

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
          network: wallet.network,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setFaucetMessage({ type: 'success', text: 'Received 1 APT from faucet' });
        // Refresh balance after a delay
        setTimeout(async () => {
          const balRes = await fetch(`${API_URL}/wallet/balance/${wallet.address}?network=${wallet.network}`);
          if (balRes.ok) {
            const balData = await balRes.json();
            setWallet((prev) => prev ? { ...prev, balance: balData.apt_balance || 0 } : null);
          }
        }, 2000);
      } else {
        setFaucetMessage({ type: 'error', text: data.error || 'Faucet request failed' });
      }
    } catch (error) {
      setFaucetMessage({ type: 'error', text: 'Network error' });
    } finally {
      setIsFaucetLoading(false);
    }
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const getNetworkColor = (network: string) => {
    switch (network) {
      case 'mainnet':
        return 'text-green-400 bg-green-500/20';
      case 'testnet':
        return 'text-yellow-400 bg-yellow-500/20';
      case 'devnet':
        return 'text-purple-400 bg-purple-500/20';
      default:
        return 'text-gray-400 bg-gray-500/20';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-800 rounded-lg">
        <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-gray-400">Loading...</span>
      </div>
    );
  }

  if (!wallet) {
    return (
      <button
        onClick={() => router.push('/login')}
        className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        Connect Wallet
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
      >
        {/* Wallet Icon */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold">
          {wallet.type[0].toUpperCase()}
        </div>
        
        {/* Address and Balance */}
        <div className="text-left">
          <p className="text-sm text-white font-medium">{formatAddress(wallet.address)}</p>
          <p className="text-xs text-gray-400">{wallet.balance.toFixed(4)} APT</p>
        </div>

        {/* Network Badge */}
        <span className={`text-xs px-2 py-0.5 rounded ${getNetworkColor(wallet.network)}`}>
          {wallet.network}
        </span>

        {/* Dropdown Arrow */}
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${showDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {showDropdown && (
        <div className="absolute right-0 top-full mt-2 w-72 bg-slate-800 rounded-xl border border-slate-700 shadow-xl z-50">
          {/* Wallet Info */}
          <div className="p-4 border-b border-slate-700">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-lg font-bold">
                {wallet.type[0].toUpperCase()}
              </div>
              <div>
                <p className="text-white font-medium capitalize">{wallet.type} Wallet</p>
                <p className="text-sm text-gray-400">{formatAddress(wallet.address)}</p>
              </div>
            </div>

            {/* Full Address */}
            <button
              onClick={() => navigator.clipboard.writeText(wallet.address)}
              className="w-full flex items-center justify-between px-3 py-2 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
            >
              <span className="text-xs text-gray-400 truncate pr-2">{wallet.address}</span>
              <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>

          {/* Balance */}
          <div className="p-4 border-b border-slate-700">
            <p className="text-xs text-gray-400 mb-1">Balance</p>
            <p className="text-2xl font-bold text-white">{wallet.balance.toFixed(4)} APT</p>
          </div>

          {/* Faucet (Testnet/Devnet only) */}
          {wallet.network !== 'mainnet' && (
            <div className="p-4 border-b border-slate-700">
              <button
                onClick={handleRequestFaucet}
                disabled={isFaucetLoading}
                className="w-full flex items-center justify-center gap-2 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors disabled:opacity-50"
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
                    <span>Request 1 APT from Faucet</span>
                  </>
                )}
              </button>

              {faucetMessage && (
                <p className={`mt-2 text-xs text-center ${faucetMessage.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                  {faucetMessage.text}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="p-2">
            <a
              href={`https://explorer.aptoslabs.com/account/${wallet.address}?network=${wallet.network}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              View on Explorer
            </a>

            <button
              onClick={handleDisconnect}
              className="w-full flex items-center gap-2 px-3 py-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Disconnect Wallet
            </button>
          </div>
        </div>
      )}

      {/* Backdrop to close dropdown */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
}
