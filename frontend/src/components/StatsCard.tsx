'use client';

import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: LucideIcon;
  color: 'red' | 'cyan' | 'green' | 'amber';
}

const colorClasses = {
  red: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    icon: 'text-red-400',
    glow: 'shadow-red-500/10',
  },
  cyan: {
    bg: 'bg-quantum-500/10',
    border: 'border-quantum-500/20',
    icon: 'text-quantum-400',
    glow: 'shadow-quantum-500/10',
  },
  green: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
    icon: 'text-green-400',
    glow: 'shadow-green-500/10',
  },
  amber: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    icon: 'text-amber-400',
    glow: 'shadow-amber-500/10',
  },
};

export default function StatsCard({ title, value, change, trend, icon: Icon, color }: StatsCardProps) {
  const colors = colorClasses[color];
  
  return (
    <div className={`card-hover group ${colors.bg} border ${colors.border} shadow-lg ${colors.glow}`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 ${colors.bg} rounded-xl border ${colors.border}`}>
          <Icon className={`w-5 h-5 ${colors.icon}`} />
        </div>
        <div className={`flex items-center gap-1 text-xs font-medium ${
          trend === 'up' ? 'text-green-400' : 'text-red-400'
        }`}>
          {trend === 'up' ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          {change}
        </div>
      </div>
      
      <h3 className="text-surface-400 text-sm mb-1">{title}</h3>
      <p className="font-display text-3xl font-bold text-surface-50 group-hover:text-quantum-300 transition-colors">
        {value}
      </p>
    </div>
  );
}

