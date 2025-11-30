'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBell } from '@fortawesome/free-solid-svg-icons';
import { WalletSelector } from './WalletSelector';

interface HeaderProps {
  title: string;
}

export default function Header({ title }: HeaderProps) {
  return (
    <header className="h-16 flex items-center justify-between px-6 bg-bg-panel border-b border-gray-800 shrink-0">
      <h2 className="text-lg font-bold text-white uppercase tracking-wide">{title}</h2>
      <div className="flex items-center space-x-4">
        <button className="px-3 py-1 bg-gray-900 border border-gray-700 rounded text-xs text-gray-400 flex items-center hover:bg-gray-700 transition">
          <FontAwesomeIcon icon={faBell} className="mr-2 text-warning" />
          3 Alerts
        </button>
        <WalletSelector />
      </div>
    </header>
  );
}
