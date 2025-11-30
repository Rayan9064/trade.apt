'use client';

import { useState, useCallback } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import Ticker from '@/components/Ticker';
import Chatbot from '@/components/Chatbot';
import ChartPanel from '@/components/ChartPanel';
import HomeView from '@/components/views/HomeView';
import AuditLogsView from '@/components/views/AuditLogsView';
import PlaceholderView from '@/components/views/PlaceholderView';

export type ViewType = 'home' | 'my_account' | 'portfolio' | 'audit_logs' | 'find_stocks';

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewType>('home');
  const [chartTokens, setChartTokens] = useState<string[]>([]);
  const [showCharts, setShowCharts] = useState(false);

  // Function to open charts (called from Chatbot via callback)
  const handleOpenCharts = useCallback((tokens: string[]) => {
    if (tokens.length > 0) {
      setChartTokens((prev) => {
        const newTokens = [...prev];
        tokens.forEach((t) => {
          const upper = t.toUpperCase();
          if (!newTokens.includes(upper)) {
            newTokens.push(upper);
          }
        });
        return newTokens;
      });
      setShowCharts(true);
    }
  }, []);

  const handleCloseCharts = useCallback(() => {
    setShowCharts(false);
    setChartTokens([]);
  }, []);

  const getPageTitle = () => {
    switch (currentView) {
      case 'home':
        return 'Home Dashboard';
      case 'my_account':
        return 'My Account Settings';
      case 'portfolio':
        return 'Portfolio Management';
      case 'audit_logs':
        return 'Audit & Compliance Logs';
      case 'find_stocks':
        return 'Stock Finder & Analyzer';
      default:
        return 'Dashboard';
    }
  };

  const renderView = () => {
    switch (currentView) {
      case 'home':
        return <HomeView />;
      case 'audit_logs':
        return <AuditLogsView />;
      case 'my_account':
        return <PlaceholderView title="My Account" />;
      case 'portfolio':
        return <PlaceholderView title="Portfolio" />;
      case 'find_stocks':
        return <PlaceholderView title="Find Specific Stocks" />;
      default:
        return <HomeView />;
    }
  };

  return (
    <div className={`grid ${showCharts ? 'grid-cols-[200px_1fr_400px_320px]' : 'grid-cols-[200px_1fr_320px]'} grid-rows-[100vh] w-screen h-screen transition-all duration-300`}>
      {/* Left Column: Navigation */}
      <Sidebar currentView={currentView} onNavigate={setCurrentView} />

      {/* Center Column: Workspace */}
      <main className="flex flex-col h-full overflow-hidden bg-black/50 relative">
        <Header title={getPageTitle()} />
        <Ticker />
        <div className="flex-grow overflow-y-auto p-6 scroll-smooth">
          {renderView()}
        </div>
      </main>

      {/* Chart Panel (conditionally rendered) */}
      {showCharts && chartTokens.length > 0 && (
        <div className="h-full overflow-hidden border-r border-gray-800">
          <ChartPanel 
            initialTokens={chartTokens} 
            onClose={handleCloseCharts}
          />
        </div>
      )}

      {/* Right Column: AI Chatbot */}
      <Chatbot onOpenCharts={handleOpenCharts} />
    </div>
  );
}
