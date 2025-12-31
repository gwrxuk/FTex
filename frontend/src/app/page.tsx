'use client';

import { useState } from 'react';
import { 
  Shield, 
  AlertTriangle, 
  Users, 
  Activity, 
  Search, 
  Bell,
  BarChart3,
  Network,
  FileText,
  Settings,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Zap,
  Globe,
  Database,
  Cpu
} from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import StatsCard from '@/components/StatsCard';
import RiskGauge from '@/components/RiskGauge';
import AlertsPanel from '@/components/AlertsPanel';
import NetworkGraph from '@/components/NetworkGraph';
import TransactionChart from '@/components/TransactionChart';
import RFPPanel from '@/components/RFPPanel';

export default function Dashboard() {
  const [selectedView, setSelectedView] = useState('dashboard');

  return (
    <div className="flex min-h-screen bg-surface-950 bg-grid">
      {/* Ambient glow effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-quantum-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
      </div>

      {/* Sidebar */}
      <Sidebar selectedView={selectedView} onSelectView={setSelectedView} />

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8 relative">
        {/* Header */}
        <header className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-bold text-surface-50 mb-1">
              Decision Intelligence
            </h1>
            <p className="text-surface-400 text-sm">
              Real-time financial crime monitoring and entity resolution
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
              <input
                type="text"
                placeholder="Search entities, transactions..."
                className="pl-10 pr-4 py-2.5 w-80 bg-surface-800/50 border border-surface-700 rounded-xl text-sm text-surface-100 placeholder:text-surface-500 focus:outline-none focus:border-quantum-500 focus:ring-1 focus:ring-quantum-500/20 transition-all"
              />
            </div>

            {/* Notifications */}
            <button className="relative p-2.5 bg-surface-800/50 border border-surface-700 rounded-xl hover:border-surface-600 transition-all">
              <Bell className="w-5 h-5 text-surface-400" />
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] font-bold flex items-center justify-center text-white">
                7
              </span>
            </button>

            {/* Profile */}
            <button className="flex items-center gap-3 px-3 py-2 bg-surface-800/50 border border-surface-700 rounded-xl hover:border-surface-600 transition-all">
              <div className="w-8 h-8 bg-gradient-to-br from-quantum-400 to-cyan-500 rounded-lg flex items-center justify-center">
                <span className="text-sm font-bold text-white">JL</span>
              </div>
              <span className="text-sm font-medium text-surface-200">Analyst</span>
            </button>
          </div>
        </header>

        {/* System Status Banner */}
        <div className="mb-6 p-4 glass rounded-xl border border-quantum-500/20 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span className="text-sm font-medium text-surface-200">All Systems Operational</span>
          </div>
          <div className="h-4 w-px bg-surface-700" />
          <div className="flex items-center gap-6 text-xs text-surface-400">
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" />
              PostgreSQL: 2.3ms
            </span>
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" />
              Spark: 12 workers
            </span>
            <span className="flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5" />
              OpenSearch: 1.8ms
            </span>
            <span className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5" />
              Neo4j: Connected
            </span>
          </div>
        </div>

        {/* RFP View */}
        {selectedView === 'rfp' && <RFPPanel />}

        {/* Dashboard View */}
        {selectedView === 'dashboard' && (
        <>
        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Active Alerts"
            value="247"
            change="+12%"
            trend="up"
            icon={AlertTriangle}
            color="red"
          />
          <StatsCard
            title="Entities Monitored"
            value="12,847"
            change="+3.2%"
            trend="up"
            icon={Users}
            color="cyan"
          />
          <StatsCard
            title="Transactions Today"
            value="1.2M"
            change="+8.5%"
            trend="up"
            icon={Activity}
            color="green"
          />
          <StatsCard
            title="Risk Score Avg"
            value="0.34"
            change="-5.1%"
            trend="down"
            icon={Shield}
            color="amber"
          />
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Network Visualization */}
          <div className="col-span-8 card min-h-[480px]">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-display text-lg font-semibold text-surface-100">Entity Network</h2>
                <p className="text-surface-500 text-sm">Real-time relationship graph</p>
              </div>
              <div className="flex items-center gap-2">
                <button className="btn-secondary text-xs">
                  Filter
                </button>
                <button className="btn-primary text-xs">
                  Expand
                </button>
              </div>
            </div>
            <NetworkGraph />
          </div>

          {/* Risk Distribution */}
          <div className="col-span-4 card">
            <h2 className="font-display text-lg font-semibold text-surface-100 mb-6">Risk Overview</h2>
            <RiskGauge score={0.67} label="Current Portfolio Risk" />
            
            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                <span className="text-sm text-red-400">Critical</span>
                <span className="text-sm font-bold text-red-300">23</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <span className="text-sm text-amber-400">High</span>
                <span className="text-sm font-bold text-amber-300">67</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-quantum-500/10 rounded-lg border border-quantum-500/20">
                <span className="text-sm text-quantum-400">Medium</span>
                <span className="text-sm font-bold text-quantum-300">134</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                <span className="text-sm text-green-400">Low</span>
                <span className="text-sm font-bold text-green-300">891</span>
              </div>
            </div>
          </div>

          {/* Transaction Volume Chart */}
          <div className="col-span-8 card">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-display text-lg font-semibold text-surface-100">Transaction Volume</h2>
                <p className="text-surface-500 text-sm">Last 30 days activity</p>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <button className="px-3 py-1.5 bg-quantum-500/20 text-quantum-400 rounded-lg">Daily</button>
                <button className="px-3 py-1.5 text-surface-400 hover:text-surface-200">Weekly</button>
                <button className="px-3 py-1.5 text-surface-400 hover:text-surface-200">Monthly</button>
              </div>
            </div>
            <TransactionChart />
          </div>

          {/* Recent Alerts */}
          <div className="col-span-4 card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-display text-lg font-semibold text-surface-100">Recent Alerts</h2>
              <button className="text-sm text-quantum-400 hover:text-quantum-300 flex items-center gap-1">
                View All
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <AlertsPanel />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 pt-6 border-t border-surface-800 flex items-center justify-between text-xs text-surface-500">
          <span>FTex Decision Intelligence Platform v1.0.0</span>
          <span>Last sync: Just now • MAS Compliant • FATF Standards</span>
        </footer>
        </>
        )}
      </main>
    </div>
  );
}

