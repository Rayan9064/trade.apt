'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

interface User {
  id: number;
  wallet_address: string;
  wallet_type: string;
  display_name: string | null;
  network: string;
  created_at: string;
  last_login: string;
  is_active: boolean;
}

interface WalletBalance {
  apt_balance: number;
  apt_balance_octas: number;
  usd_value: number | null;
}

interface AuthContextType {
  user: User | null;
  sessionToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  walletAddress: string | null;
  walletBalance: WalletBalance | null;
  network: 'mainnet' | 'testnet' | 'devnet';
  login: (walletAddress: string, walletType?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshBalance: () => Promise<void>;
  setNetwork: (network: 'mainnet' | 'testnet' | 'devnet') => void;
  requestFaucet: (amount?: number) => Promise<{ success: boolean; message: string }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [walletBalance, setWalletBalance] = useState<WalletBalance | null>(null);
  const [network, setNetworkState] = useState<'mainnet' | 'testnet' | 'devnet'>('testnet');

  // Load session from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('session_token');
    const storedNetwork = localStorage.getItem('network') as 'mainnet' | 'testnet' | 'devnet';
    
    if (storedNetwork) {
      setNetworkState(storedNetwork);
    }
    
    if (storedToken) {
      validateSession(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const validateSession = async (token: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/session`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setSessionToken(token);
        // Fetch balance after validating session
        if (data.user?.wallet_address) {
          fetchBalance(data.user.wallet_address);
        }
      } else {
        // Invalid session, clear storage
        localStorage.removeItem('session_token');
      }
    } catch (error) {
      console.error('Session validation error:', error);
      localStorage.removeItem('session_token');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchBalance = async (address: string) => {
    try {
      const response = await fetch(`${API_URL}/wallet/balance/${address}?network=${network}`);
      if (response.ok) {
        const data = await response.json();
        setWalletBalance({
          apt_balance: data.apt_balance,
          apt_balance_octas: data.apt_balance_octas,
          usd_value: data.usd_value,
        });
      }
    } catch (error) {
      console.error('Balance fetch error:', error);
    }
  };

  const login = useCallback(async (walletAddress: string, walletType: string = 'petra'): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallet_address: walletAddress,
          wallet_type: walletType,
          network: network,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setUser(data.user);
          setSessionToken(data.session_token);
          localStorage.setItem('session_token', data.session_token);
          
          // Fetch balance
          fetchBalance(walletAddress);
          
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  }, [network]);

  const logout = useCallback(async () => {
    if (sessionToken) {
      try {
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${sessionToken}`,
          },
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    setUser(null);
    setSessionToken(null);
    setWalletBalance(null);
    localStorage.removeItem('session_token');
  }, [sessionToken]);

  const refreshBalance = useCallback(async () => {
    if (user?.wallet_address) {
      await fetchBalance(user.wallet_address);
    }
  }, [user, network]);

  const setNetwork = useCallback((newNetwork: 'mainnet' | 'testnet' | 'devnet') => {
    setNetworkState(newNetwork);
    localStorage.setItem('network', newNetwork);
    // Refresh balance for new network
    if (user?.wallet_address) {
      fetchBalance(user.wallet_address);
    }
  }, [user]);

  const requestFaucet = useCallback(async (amount: number = 1): Promise<{ success: boolean; message: string }> => {
    if (!user?.wallet_address) {
      return { success: false, message: 'No wallet connected' };
    }

    if (network === 'mainnet') {
      return { success: false, message: 'Faucet not available on mainnet' };
    }

    try {
      const response = await fetch(`${API_URL}/wallet/faucet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address: user.wallet_address,
          amount_apt: amount,
          network: network,
        }),
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        // Refresh balance after faucet
        setTimeout(() => refreshBalance(), 2000);
        return { success: true, message: data.message || `Received ${amount} APT` };
      } else {
        return { success: false, message: data.detail || data.error || 'Faucet request failed' };
      }
    } catch (error) {
      console.error('Faucet error:', error);
      return { success: false, message: 'Network error' };
    }
  }, [user, network, refreshBalance]);

  const value: AuthContextType = {
    user,
    sessionToken,
    isAuthenticated: !!user && !!sessionToken,
    isLoading,
    walletAddress: user?.wallet_address || null,
    walletBalance,
    network,
    login,
    logout,
    refreshBalance,
    setNetwork,
    requestFaucet,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
