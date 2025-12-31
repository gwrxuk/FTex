'use client';

import { 
  LayoutDashboard, 
  Users, 
  ArrowLeftRight, 
  AlertTriangle, 
  FolderKanban,
  Search,
  Network,
  BarChart3,
  Settings,
  HelpCircle,
  LogOut,
  Zap,
  FileText
} from 'lucide-react';

interface SidebarProps {
  selectedView: string;
  onSelectView: (view: string) => void;
}

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'entities', label: 'Entity Resolution', icon: Users },
  { id: 'transactions', label: 'Transactions', icon: ArrowLeftRight },
  { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
  { id: 'cases', label: 'Cases', icon: FolderKanban },
  { id: 'rfp', label: 'RFPs & RFIs', icon: FileText },
  { id: 'search', label: 'Global Search', icon: Search },
  { id: 'graph', label: 'Network Analysis', icon: Network },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
];

const bottomItems = [
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'help', label: 'Help & Support', icon: HelpCircle },
];

export default function Sidebar({ selectedView, onSelectView }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-surface-900/95 backdrop-blur-xl border-r border-surface-800 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-surface-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-quantum-400 via-cyan-400 to-teal-400 rounded-xl flex items-center justify-center shadow-lg shadow-quantum-500/20">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-display text-xl font-bold bg-gradient-to-r from-quantum-400 to-cyan-400 bg-clip-text text-transparent">
              FTex
            </h1>
            <p className="text-[10px] text-surface-500 uppercase tracking-widest">Decision Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = selectedView === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onSelectView(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-quantum-500/20 to-cyan-500/10 text-quantum-400 border border-quantum-500/30'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/50'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-quantum-400' : ''}`} />
              {item.label}
              {item.id === 'alerts' && (
                <span className="ml-auto px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-bold rounded-full">
                  12
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-surface-800 space-y-1">
        {bottomItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onSelectView(item.id)}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-surface-400 hover:text-surface-200 hover:bg-surface-800/50 transition-all"
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </button>
          );
        })}
        
        <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all mt-2">
          <LogOut className="w-5 h-5" />
          Sign Out
        </button>
      </div>

      {/* Version */}
      <div className="p-4 border-t border-surface-800">
        <div className="p-3 bg-surface-800/50 rounded-xl">
          <div className="flex items-center justify-between text-xs">
            <span className="text-surface-500">Version</span>
            <span className="text-surface-400">1.0.0</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="text-surface-500">Environment</span>
            <span className="text-green-400">Production</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

