'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faChartLine,
  faHome,
  faUserShield,
  faBriefcase,
  faListCheck,
  faMagnifyingGlass,
  faWallet,
} from '@fortawesome/free-solid-svg-icons';
import type { ViewType } from '@/app/page';

interface SidebarProps {
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
}

const navItems: { id: ViewType; label: string; icon: any }[] = [
  { id: 'home', label: 'HOME', icon: faHome },
  { id: 'my_account', label: 'MY ACCOUNT', icon: faUserShield },
  { id: 'portfolio', label: 'PORTFOLIO', icon: faBriefcase },
  { id: 'audit_logs', label: 'AUDIT LOGS', icon: faListCheck },
  { id: 'find_stocks', label: 'FIND SPECIFIC STOCKS', icon: faMagnifyingGlass },
];

export default function Sidebar({ currentView, onNavigate }: SidebarProps) {
  const [walletAddress, setWalletAddress] = useState<string | null>(null);

  useEffect(() => {
    const address = localStorage.getItem('wallet_address');
    setWalletAddress(address);
  }, []);

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <nav className="panel-border border-l-0 border-t-0 border-b-0 bg-bg-panel flex flex-col z-20">
      {/* Brand */}
      <div className="h-16 flex items-center px-4 border-b border-gray-800">
        <FontAwesomeIcon icon={faChartLine} className="text-aptos-blue text-2xl mr-2" />
        <span className="font-bold text-lg tracking-wider text-white">Trade.apt</span>
      </div>

      {/* Menu Links */}
      <div className="flex-grow py-6 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center px-3 py-2.5 rounded-lg transition-all group ${
                isActive
                  ? 'text-aptos-blue bg-gray-800/50 border border-gray-700 shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800 border border-transparent'
              }`}
            >
              <FontAwesomeIcon
                icon={item.icon}
                className={`w-6 text-center mr-3 ${isActive ? 'text-aptos-blue' : 'group-hover:text-aptos-blue'}`}
              />
              <span className={`text-sm ${isActive ? 'font-bold' : 'font-medium'}`}>{item.label}</span>
            </button>
          );
        })}

        {/* Wallet Management Link */}
        <Link
          href="/wallet"
          className="w-full flex items-center px-3 py-2.5 rounded-lg transition-all group text-gray-400 hover:text-white hover:bg-gray-800 border border-transparent"
        >
          <FontAwesomeIcon
            icon={faWallet}
            className="w-6 text-center mr-3 group-hover:text-aptos-blue"
          />
          <span className="text-sm font-medium">WALLET</span>
        </Link>
      </div>

      {/* User Footer */}
      <div className="p-4 border-t border-gray-800 bg-black/20">
        {walletAddress ? (
          <Link href="/wallet" className="flex items-center hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-aptos-blue to-purple-600 flex items-center justify-center text-xs font-bold text-white">
              {walletAddress.slice(2, 4).toUpperCase()}
            </div>
            <div className="ml-3 overflow-hidden">
              <p className="text-xs text-white font-semibold">{formatAddress(walletAddress)}</p>
              <p className="text-[10px] text-green-400">Connected</p>
            </div>
          </Link>
        ) : (
          <Link href="/login" className="flex items-center hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-400">
              ?
            </div>
            <div className="ml-3 overflow-hidden">
              <p className="text-xs text-gray-400 font-semibold">Not Connected</p>
              <p className="text-[10px] text-yellow-400">Click to Connect</p>
            </div>
          </Link>
        )}
      </div>
    </nav>
  );
}
