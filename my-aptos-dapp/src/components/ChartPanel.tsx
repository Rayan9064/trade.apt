'use client';

import React, { useState, useCallback } from 'react';
import CoinChart from './CoinChart';

interface ChartTab {
  symbol: string;
  id: string;
}

interface ChartPanelProps {
  initialTokens?: string[];
  onClose?: () => void;
}

const ChartPanel: React.FC<ChartPanelProps> = ({ initialTokens = [], onClose }) => {
  const [tabs, setTabs] = useState<ChartTab[]>(
    initialTokens.map((symbol) => ({
      symbol: symbol.toUpperCase(),
      id: `${symbol}-${Date.now()}`,
    }))
  );
  const [activeTabId, setActiveTabId] = useState<string | null>(
    tabs.length > 0 ? tabs[0].id : null
  );

  const removeTab = useCallback((id: string) => {
    setTabs((prev) => {
      const newTabs = prev.filter((t) => t.id !== id);
      if (activeTabId === id && newTabs.length > 0) {
        setActiveTabId(newTabs[newTabs.length - 1].id);
      } else if (newTabs.length === 0) {
        onClose?.();
      }
      return newTabs;
    });
  }, [activeTabId, onClose]);

  const activeTab = tabs.find((t) => t.id === activeTabId);

  if (tabs.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col h-full bg-gray-950 rounded-xl overflow-hidden border border-gray-800">
      {/* Tab Bar */}
      <div className="flex items-center bg-gray-900 border-b border-gray-800 overflow-x-auto">
        <div className="flex items-center flex-1 min-w-0">
          {tabs.map((tab) => (
            <div
              key={tab.id}
              className={`flex items-center gap-2 px-4 py-2.5 cursor-pointer border-r border-gray-800 min-w-[120px] max-w-[180px] ${
                activeTabId === tab.id
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-900 text-gray-400 hover:bg-gray-850 hover:text-white'
              }`}
              onClick={() => setActiveTabId(tab.id)}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <div className={`w-2 h-2 rounded-full ${
                  activeTabId === tab.id ? 'bg-green-400' : 'bg-gray-600'
                }`}></div>
                <span className="font-medium truncate">{tab.symbol}/USD</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeTab(tab.id);
                }}
                className="p-1 hover:bg-gray-700 rounded transition-colors flex-shrink-0"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Close All Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors flex-shrink-0"
            title="Close all charts"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Chart Content */}
      <div className="flex-1 min-h-0">
        {activeTab && (
          <CoinChart
            key={activeTab.id}
            symbol={activeTab.symbol}
            onClose={() => removeTab(activeTab.id)}
          />
        )}
      </div>
    </div>
  );
};

// Export a helper hook to manage chart panel from parent components
export const useChartPanel = () => {
  const [tokens, setTokens] = useState<string[]>([]);
  const [isVisible, setIsVisible] = useState(false);

  const openCharts = useCallback((symbols: string[]) => {
    setTokens((prev) => {
      const newTokens = [...prev];
      symbols.forEach((s) => {
        const upper = s.toUpperCase();
        if (!newTokens.includes(upper)) {
          newTokens.push(upper);
        }
      });
      return newTokens;
    });
    setIsVisible(true);
  }, []);

  const closeCharts = useCallback(() => {
    setIsVisible(false);
    setTokens([]);
  }, []);

  const addChart = useCallback((symbol: string) => {
    const upper = symbol.toUpperCase();
    setTokens((prev) => {
      if (prev.includes(upper)) return prev;
      return [...prev, upper];
    });
    setIsVisible(true);
  }, []);

  return {
    tokens,
    isVisible,
    openCharts,
    closeCharts,
    addChart,
  };
};

export default ChartPanel;
