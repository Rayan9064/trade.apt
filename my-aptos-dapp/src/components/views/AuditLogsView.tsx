'use client';

import { useState, useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faRobot, faUser, faChevronDown } from '@fortawesome/free-solid-svg-icons';

Chart.register(...registerables);

// Types
interface AuditLog {
  id: string;
  timestamp: string;
  log_category: string;
  status: string;
  smart_contract_hash: string | null;
  actor_id: string;
  description: string;
  action_type?: string;
  ai_reason?: string;
}

// Categories
const ALL_CATEGORIES = [
  'ALL',
  'TRADE_EXECUTION',
  'PERMISSION_CHANGE',
  'RULE_CREATION',
  'LIQUIDITY_CHANGE',
  'VAULT_INTERACTION',
  'AI_DECISION',
  'ERROR_SECURITY',
  'USER_ACTIVITY',
];

// Mock data generator
const generateAuditLogs = (): AuditLog[] => {
  const categoriesMap = [
    { id: 'TRADE_EXECUTION', prefix: 'TRD' },
    { id: 'RULE_CREATION', prefix: 'RULE' },
    { id: 'AI_DECISION', prefix: 'AI' },
    { id: 'ERROR_SECURITY', prefix: 'SEC' },
    { id: 'USER_ACTIVITY', prefix: 'USR' },
  ];

  const logs: AuditLog[] = [];
  const now = new Date();
  const mockHash = () => '0x' + Math.random().toString(16).substr(2, 64);

  for (let i = 0; i < 60; i++) {
    const cat = categoriesMap[Math.floor(Math.random() * categoriesMap.length)];
    const time = new Date(now.getTime() - i * Math.random() * 7200000);

    const log: AuditLog = {
      id: `${cat.prefix}-${1000 + i}`,
      timestamp: time.toISOString(),
      log_category: cat.id,
      status: Math.random() > 0.1 ? 'Success' : Math.random() > 0.5 ? 'Failed' : 'Blocked',
      smart_contract_hash: Math.random() > 0.3 ? mockHash() : null,
      actor_id: Math.random() > 0.5 ? 'User-0x8...A9' : 'AI (Auto Mode)',
      description: 'Mock Log Event Description',
    };

    switch (cat.id) {
      case 'TRADE_EXECUTION':
        log.action_type = ['BUY BTC', 'SELL ETH'][Math.floor(Math.random() * 2)];
        log.description = `Executed trade: ${log.action_type} for $${(Math.random() * 5000).toFixed(2)}`;
        break;
      case 'RULE_CREATION':
        log.action_type = 'RULE_CREATED';
        log.description = 'New Rule: Sell if BTC drops 5% in 1 hour';
        break;
      case 'AI_DECISION':
        log.action_type = 'SUGGESTION_MADE';
        log.ai_reason = 'MACD crossover detected';
        log.description = 'AI Suggested: Increase BTC allocation by 10%';
        break;
      case 'ERROR_SECURITY':
        log.action_type = 'API_AUTH_FAILED';
        log.description = 'Security alert: Failed attempt to modify trade limit';
        log.status = 'Blocked';
        break;
      case 'USER_ACTIVITY':
        log.action_type = 'SETTINGS_CHANGE';
        log.description = 'User updated notification preferences';
        break;
    }
    logs.push(log);
  }
  return logs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
};

export default function AuditLogsView() {
  const [logs] = useState<AuditLog[]>(generateAuditLogs);
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  // Filtered data
  const filteredLogs = logs.filter((log) => {
    const matchCat = categoryFilter === 'ALL' || log.log_category === categoryFilter;
    const matchSearch = log.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchSearch;
  });

  // Stats
  const totalEvents = logs.length;
  const securityFlags = logs.filter((l) => l.log_category === 'ERROR_SECURITY').length;
  const aiActions = logs.filter((l) => l.actor_id.includes('AI')).length;

  // Chart
  useEffect(() => {
    if (!chartRef.current) return;

    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const categoryCounts: Record<string, number> = {};
    logs.forEach((log) => {
      categoryCounts[log.log_category] = (categoryCounts[log.log_category] || 0) + 1;
    });

    const sortedCategories = Object.keys(categoryCounts).sort();
    const sortedCounts = sortedCategories.map((cat) => categoryCounts[cat]);

    chartInstance.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: sortedCategories.map((k) => k.replace('_', ' ')),
        datasets: [
          {
            label: 'Events Count',
            data: sortedCounts,
            backgroundColor: '#0A98F7',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { grid: { color: '#1F2937' }, ticks: { color: '#9CA3AF' }, beginAtZero: true },
          x: { grid: { display: false }, ticks: { color: '#9CA3AF' } },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [logs]);

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'Success':
        return 'bg-green-900/30 text-green-400';
      case 'Failed':
        return 'bg-red-900/30 text-red-400';
      case 'Blocked':
        return 'bg-yellow-900/30 text-yellow-400';
      default:
        return 'bg-gray-900/30 text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-bg-panel panel-border rounded-xl p-4 shadow-lg flex flex-col">
          <h3 className="text-sm font-bold text-gray-400 uppercase mb-2">Audit Event Distribution</h3>
          <div className="chart-container">
            <canvas ref={chartRef}></canvas>
          </div>
        </div>
        <div className="bg-bg-panel panel-border rounded-xl p-6 shadow-lg flex flex-col justify-center space-y-4">
          <div>
            <p className="text-xs text-gray-500 uppercase">Total Events Logged</p>
            <p className="text-3xl font-bold text-white">{totalEvents}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Security Flags</p>
            <p className="text-2xl font-bold text-danger">{securityFlags}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">AI Actions</p>
            <p className="text-2xl font-bold text-aptos-blue">{aiActions}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-bg-panel panel-border p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center justify-between shadow-lg sticky top-0 z-10">
        <div className="flex gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {ALL_CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded text-[10px] font-bold uppercase whitespace-nowrap transition-colors ${
                categoryFilter === cat
                  ? 'bg-aptos-blue text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
        <div className="relative w-full md:w-64">
          <input
            type="text"
            placeholder="Search hash, type, desc..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-black border border-gray-700 text-gray-300 text-xs rounded-lg pl-8 pr-3 py-2 focus:border-aptos-blue focus:ring-1 focus:ring-aptos-blue outline-none"
          />
          <FontAwesomeIcon icon={faSearch} className="absolute left-2.5 top-2.5 text-gray-500 text-xs" />
        </div>
      </div>

      {/* Data Grid (Table) */}
      <div className="bg-bg-panel panel-border rounded-xl shadow-xl overflow-hidden min-h-[400px]">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-900/50 border-b border-gray-800 text-[10px] uppercase text-gray-500 tracking-wider">
                <th className="px-6 py-4 font-semibold">Time (UTC)</th>
                <th className="px-6 py-4 font-semibold">Category</th>
                <th className="px-6 py-4 font-semibold">Description</th>
                <th className="px-6 py-4 font-semibold">Actor</th>
                <th className="px-6 py-4 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800 text-xs">
              {filteredLogs.map((log) => (
                <>
                  <tr
                    key={log.id}
                    onClick={() => setExpandedRow(expandedRow === log.id ? null : log.id)}
                    className="log-row transition-colors group"
                  >
                    <td className="px-6 py-3 text-gray-400 font-mono whitespace-nowrap">
                      {log.timestamp.replace('T', ' ').substring(0, 19)}
                    </td>
                    <td className="px-6 py-3">
                      <span className="text-xs font-bold text-gray-300 bg-gray-800/50 px-2 py-1 rounded">
                        {log.log_category.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      <div className="text-gray-400 truncate max-w-xs">{log.description}</div>
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex items-center">
                        <FontAwesomeIcon
                          icon={log.actor_id.includes('AI') ? faRobot : faUser}
                          className={`mr-2 ${log.actor_id.includes('AI') ? 'text-aptos-blue' : 'text-purple-400'}`}
                        />
                        <span className="text-gray-400">{log.actor_id}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3 text-right">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusBadgeClass(log.status)}`}>
                        {log.status}
                      </span>
                      <FontAwesomeIcon
                        icon={faChevronDown}
                        className={`ml-2 text-gray-600 group-hover:text-white transition-transform ${
                          expandedRow === log.id ? 'rotate-180' : ''
                        }`}
                      />
                    </td>
                  </tr>
                  {expandedRow === log.id && (
                    <tr key={`${log.id}-detail`} className="detail-row">
                      <td colSpan={5} className="px-6 py-4">
                        <div className="grid grid-cols-2 gap-4 text-gray-300">
                          <div>
                            <p className="text-[10px] text-gray-500 uppercase mb-1">Transaction Hash</p>
                            <p className="font-mono text-aptos-blue break-all select-all">
                              {log.smart_contract_hash || 'Off-chain Event'}
                            </p>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
