'use client';

import { useEffect, useRef } from 'react';

interface DataPoint {
  date: string;
  volume: number;
  flagged: number;
}

// Generate demo data
const generateChartData = (): DataPoint[] => {
  const data: DataPoint[] = [];
  const now = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    data.push({
      date: date.toISOString().split('T')[0],
      volume: Math.floor(800000 + Math.random() * 600000 + Math.sin(i / 5) * 200000),
      flagged: Math.floor(50 + Math.random() * 150),
    });
  }
  
  return data;
};

export default function TransactionChart() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);
    
    const data = generateChartData();
    const padding = { top: 30, right: 20, bottom: 40, left: 60 };
    const chartWidth = rect.width - padding.left - padding.right;
    const chartHeight = rect.height - padding.top - padding.bottom;
    
    const maxVolume = Math.max(...data.map(d => d.volume));
    const maxFlagged = Math.max(...data.map(d => d.flagged));
    
    // Animation
    let progress = 0;
    const animate = () => {
      progress += 0.03;
      if (progress > 1) progress = 1;
      
      ctx.clearRect(0, 0, rect.width, rect.height);
      
      // Draw grid lines
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.3)';
      ctx.lineWidth = 1;
      
      for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(rect.width - padding.right, y);
        ctx.stroke();
        
        // Y-axis labels
        const value = maxVolume - (maxVolume / 4) * i;
        ctx.fillStyle = '#64748b';
        ctx.font = '10px JetBrains Mono';
        ctx.textAlign = 'right';
        ctx.fillText(formatNumber(value), padding.left - 10, y + 4);
      }
      
      // Draw area chart (volume)
      const gradient = ctx.createLinearGradient(0, padding.top, 0, rect.height - padding.bottom);
      gradient.addColorStop(0, 'rgba(14, 165, 233, 0.3)');
      gradient.addColorStop(1, 'rgba(14, 165, 233, 0.0)');
      
      ctx.beginPath();
      ctx.moveTo(padding.left, rect.height - padding.bottom);
      
      data.forEach((point, i) => {
        const x = padding.left + (chartWidth / (data.length - 1)) * i;
        const y = padding.top + chartHeight - (point.volume / maxVolume) * chartHeight * progress;
        
        if (i === 0) {
          ctx.lineTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      
      ctx.lineTo(rect.width - padding.right, rect.height - padding.bottom);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();
      
      // Draw line (volume)
      ctx.beginPath();
      ctx.strokeStyle = '#0ea5e9';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      
      data.forEach((point, i) => {
        const x = padding.left + (chartWidth / (data.length - 1)) * i;
        const y = padding.top + chartHeight - (point.volume / maxVolume) * chartHeight * progress;
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();
      
      // Draw flagged transactions bars
      const barWidth = chartWidth / data.length * 0.6;
      
      data.forEach((point, i) => {
        const x = padding.left + (chartWidth / (data.length - 1)) * i - barWidth / 2;
        const barHeight = (point.flagged / maxFlagged) * (chartHeight * 0.3) * progress;
        const y = rect.height - padding.bottom - barHeight;
        
        ctx.fillStyle = 'rgba(239, 68, 68, 0.5)';
        ctx.fillRect(x, y, barWidth, barHeight);
      });
      
      // Draw data points
      data.forEach((point, i) => {
        const x = padding.left + (chartWidth / (data.length - 1)) * i;
        const y = padding.top + chartHeight - (point.volume / maxVolume) * chartHeight * progress;
        
        // Glow
        const glow = ctx.createRadialGradient(x, y, 0, x, y, 8);
        glow.addColorStop(0, 'rgba(14, 165, 233, 0.5)');
        glow.addColorStop(1, 'rgba(14, 165, 233, 0)');
        
        ctx.beginPath();
        ctx.fillStyle = glow;
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fill();
        
        // Point
        ctx.beginPath();
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = '#0ea5e9';
        ctx.lineWidth = 2;
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      });
      
      // X-axis labels (every 5 days)
      ctx.fillStyle = '#64748b';
      ctx.font = '10px JetBrains Mono';
      ctx.textAlign = 'center';
      
      data.forEach((point, i) => {
        if (i % 5 === 0 || i === data.length - 1) {
          const x = padding.left + (chartWidth / (data.length - 1)) * i;
          const date = new Date(point.date);
          const label = `${date.getMonth() + 1}/${date.getDate()}`;
          ctx.fillText(label, x, rect.height - padding.bottom + 20);
        }
      });
      
      // Legend
      ctx.font = '11px JetBrains Mono';
      ctx.textAlign = 'left';
      
      // Volume legend
      ctx.fillStyle = '#0ea5e9';
      ctx.beginPath();
      ctx.arc(padding.left + 10, 15, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#94a3b8';
      ctx.fillText('Transaction Volume', padding.left + 22, 19);
      
      // Flagged legend
      ctx.fillStyle = 'rgba(239, 68, 68, 0.5)';
      ctx.fillRect(padding.left + 160, 11, 12, 8);
      ctx.fillStyle = '#94a3b8';
      ctx.fillText('Flagged', padding.left + 178, 19);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    animate();
  }, []);
  
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
    return num.toString();
  };
  
  return (
    <div className="w-full h-[240px]">
      <canvas 
        ref={canvasRef}
        className="w-full h-full"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

