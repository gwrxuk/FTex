'use client';

interface RiskGaugeProps {
  score: number;
  label: string;
}

export default function RiskGauge({ score, label }: RiskGaugeProps) {
  const percentage = score * 100;
  const rotation = (score * 180) - 90;
  
  const getRiskColor = (score: number) => {
    if (score >= 0.8) return '#dc2626'; // red
    if (score >= 0.6) return '#ea580c'; // orange
    if (score >= 0.4) return '#f59e0b'; // amber
    if (score >= 0.2) return '#22c55e'; // green
    return '#14b8a6'; // teal
  };
  
  const getRiskLabel = (score: number) => {
    if (score >= 0.8) return 'Critical';
    if (score >= 0.6) return 'High';
    if (score >= 0.4) return 'Medium';
    if (score >= 0.2) return 'Low';
    return 'Minimal';
  };

  const color = getRiskColor(score);
  
  return (
    <div className="flex flex-col items-center">
      {/* Gauge */}
      <div className="relative w-48 h-24 mb-4">
        {/* Background arc */}
        <svg className="w-full h-full" viewBox="0 0 200 100">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#14b8a6" />
              <stop offset="25%" stopColor="#22c55e" />
              <stop offset="50%" stopColor="#f59e0b" />
              <stop offset="75%" stopColor="#ea580c" />
              <stop offset="100%" stopColor="#dc2626" />
            </linearGradient>
          </defs>
          
          {/* Background track */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="#1e293b"
            strokeWidth="12"
            strokeLinecap="round"
          />
          
          {/* Colored arc */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray="251.2"
            strokeDashoffset={251.2 * (1 - score)}
            className="transition-all duration-1000 ease-out"
          />
          
          {/* Tick marks */}
          {[0, 0.25, 0.5, 0.75, 1].map((tick, i) => {
            const angle = (tick * 180) - 90;
            const rad = (angle * Math.PI) / 180;
            const x1 = 100 + 65 * Math.cos(rad);
            const y1 = 90 + 65 * Math.sin(rad);
            const x2 = 100 + 75 * Math.cos(rad);
            const y2 = 90 + 75 * Math.sin(rad);
            
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#475569"
                strokeWidth="2"
              />
            );
          })}
        </svg>
        
        {/* Needle */}
        <div 
          className="absolute bottom-0 left-1/2 w-1 h-16 -ml-0.5 origin-bottom transition-transform duration-1000 ease-out"
          style={{ 
            transform: `rotate(${rotation}deg)`,
          }}
        >
          <div 
            className="w-full h-full rounded-t-full"
            style={{ backgroundColor: color }}
          />
        </div>
        
        {/* Center dot */}
        <div 
          className="absolute bottom-0 left-1/2 w-4 h-4 -ml-2 -mb-2 rounded-full border-2"
          style={{ 
            backgroundColor: color,
            borderColor: color,
            boxShadow: `0 0 12px ${color}80`
          }}
        />
      </div>
      
      {/* Score display */}
      <div className="text-center">
        <div className="font-display text-4xl font-bold" style={{ color }}>
          {(score * 100).toFixed(0)}%
        </div>
        <div 
          className="text-sm font-semibold mt-1"
          style={{ color }}
        >
          {getRiskLabel(score)} Risk
        </div>
        <div className="text-xs text-surface-500 mt-1">
          {label}
        </div>
      </div>
    </div>
  );
}

