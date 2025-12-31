'use client';

import { AlertTriangle, Clock, User, ChevronRight } from 'lucide-react';

const alerts = [
  {
    id: 1,
    title: 'High-risk transaction pattern detected',
    severity: 'critical',
    entity: 'Entity #4521',
    time: '2 min ago',
    type: 'Transaction Monitoring',
  },
  {
    id: 2,
    title: 'Sanctions list match - PEP screening',
    severity: 'high',
    entity: 'Entity #8834',
    time: '15 min ago',
    type: 'Screening',
  },
  {
    id: 3,
    title: 'Unusual velocity spike detected',
    severity: 'medium',
    entity: 'Entity #2198',
    time: '1 hour ago',
    type: 'Behavioral',
  },
  {
    id: 4,
    title: 'Cross-border activity threshold exceeded',
    severity: 'high',
    entity: 'Entity #6742',
    time: '2 hours ago',
    type: 'Threshold',
  },
  {
    id: 5,
    title: 'Network cluster anomaly identified',
    severity: 'medium',
    entity: 'Cluster #12',
    time: '3 hours ago',
    type: 'Network',
  },
];

const severityColors = {
  critical: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    dot: 'bg-red-500',
    pulse: 'risk-pulse-critical',
  },
  high: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    dot: 'bg-amber-500',
    pulse: '',
  },
  medium: {
    bg: 'bg-quantum-500/10',
    border: 'border-quantum-500/30',
    text: 'text-quantum-400',
    dot: 'bg-quantum-500',
    pulse: '',
  },
  low: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
    dot: 'bg-green-500',
    pulse: '',
  },
};

export default function AlertsPanel() {
  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const colors = severityColors[alert.severity as keyof typeof severityColors];
        
        return (
          <div
            key={alert.id}
            className={`p-4 rounded-xl ${colors.bg} border ${colors.border} cursor-pointer hover:scale-[1.02] transition-all group`}
          >
            <div className="flex items-start gap-3">
              <div className={`relative mt-0.5`}>
                <div className={`w-2.5 h-2.5 rounded-full ${colors.dot} ${colors.pulse}`} />
              </div>
              
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-surface-100 truncate group-hover:text-quantum-300 transition-colors">
                  {alert.title}
                </h4>
                
                <div className="flex items-center gap-3 mt-2 text-xs text-surface-500">
                  <span className="flex items-center gap-1">
                    <User className="w-3 h-3" />
                    {alert.entity}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {alert.time}
                  </span>
                </div>
                
                <div className="mt-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide ${colors.bg} ${colors.text} border ${colors.border}`}>
                    {alert.type}
                  </span>
                </div>
              </div>
              
              <ChevronRight className="w-4 h-4 text-surface-600 group-hover:text-surface-400 transition-colors" />
            </div>
          </div>
        );
      })}
    </div>
  );
}

