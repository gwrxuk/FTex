'use client';

import { useEffect, useRef } from 'react';

interface Node {
  id: string;
  label: string;
  type: string;
  risk: number;
  x: number;
  y: number;
}

interface Edge {
  source: string;
  target: string;
  type: string;
}

// Generate demo network data
const generateNetworkData = () => {
  const nodes: Node[] = [
    { id: '1', label: 'Entity A', type: 'organization', risk: 0.8, x: 400, y: 200 },
    { id: '2', label: 'Entity B', type: 'individual', risk: 0.3, x: 250, y: 150 },
    { id: '3', label: 'Entity C', type: 'individual', risk: 0.6, x: 550, y: 150 },
    { id: '4', label: 'Account 1', type: 'account', risk: 0.4, x: 300, y: 300 },
    { id: '5', label: 'Account 2', type: 'account', risk: 0.9, x: 500, y: 300 },
    { id: '6', label: 'Entity D', type: 'organization', risk: 0.2, x: 150, y: 250 },
    { id: '7', label: 'Entity E', type: 'individual', risk: 0.7, x: 650, y: 250 },
    { id: '8', label: 'Account 3', type: 'account', risk: 0.5, x: 400, y: 350 },
  ];
  
  const edges: Edge[] = [
    { source: '1', target: '2', type: 'owns' },
    { source: '1', target: '3', type: 'owns' },
    { source: '1', target: '4', type: 'transacted' },
    { source: '1', target: '5', type: 'transacted' },
    { source: '2', target: '4', type: 'owns' },
    { source: '3', target: '5', type: 'owns' },
    { source: '2', target: '6', type: 'related' },
    { source: '3', target: '7', type: 'related' },
    { source: '4', target: '5', type: 'transacted' },
    { source: '4', target: '8', type: 'transacted' },
    { source: '5', target: '8', type: 'transacted' },
  ];
  
  return { nodes, edges };
};

const getRiskColor = (risk: number) => {
  if (risk >= 0.8) return '#dc2626';
  if (risk >= 0.6) return '#ea580c';
  if (risk >= 0.4) return '#f59e0b';
  if (risk >= 0.2) return '#22c55e';
  return '#14b8a6';
};

const getTypeColor = (type: string) => {
  switch (type) {
    case 'organization': return '#0ea5e9';
    case 'individual': return '#8b5cf6';
    case 'account': return '#10b981';
    default: return '#64748b';
  }
};

export default function NetworkGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  
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
    
    const { nodes, edges } = generateNetworkData();
    let time = 0;
    
    const draw = () => {
      ctx.clearRect(0, 0, rect.width, rect.height);
      
      // Draw background grid
      ctx.strokeStyle = 'rgba(14, 165, 233, 0.03)';
      ctx.lineWidth = 1;
      for (let x = 0; x < rect.width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, rect.height);
        ctx.stroke();
      }
      for (let y = 0; y < rect.height; y += 40) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(rect.width, y);
        ctx.stroke();
      }
      
      // Draw edges
      edges.forEach((edge) => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);
        if (!source || !target) return;
        
        // Animated flow effect
        const gradient = ctx.createLinearGradient(source.x, source.y, target.x, target.y);
        const flowPos = (Math.sin(time * 2 + parseInt(edge.source)) + 1) / 2;
        
        gradient.addColorStop(0, 'rgba(14, 165, 233, 0.1)');
        gradient.addColorStop(Math.max(0, flowPos - 0.1), 'rgba(14, 165, 233, 0.1)');
        gradient.addColorStop(flowPos, 'rgba(14, 165, 233, 0.6)');
        gradient.addColorStop(Math.min(1, flowPos + 0.1), 'rgba(14, 165, 233, 0.1)');
        gradient.addColorStop(1, 'rgba(14, 165, 233, 0.1)');
        
        ctx.beginPath();
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 2;
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      });
      
      // Draw nodes
      nodes.forEach((node) => {
        const x = node.x + Math.sin(time + parseInt(node.id)) * 2;
        const y = node.y + Math.cos(time + parseInt(node.id)) * 2;
        
        // Risk glow
        const riskColor = getRiskColor(node.risk);
        const glowSize = 30 + node.risk * 20;
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, glowSize);
        gradient.addColorStop(0, riskColor + '40');
        gradient.addColorStop(1, riskColor + '00');
        
        ctx.beginPath();
        ctx.fillStyle = gradient;
        ctx.arc(x, y, glowSize, 0, Math.PI * 2);
        ctx.fill();
        
        // Node circle
        ctx.beginPath();
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = getTypeColor(node.type);
        ctx.lineWidth = 3;
        ctx.arc(x, y, 20, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        
        // Risk indicator
        ctx.beginPath();
        ctx.fillStyle = riskColor;
        ctx.arc(x + 14, y - 14, 6, 0, Math.PI * 2);
        ctx.fill();
        
        // Label
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '11px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, x, y + 35);
        
        // Type icon (simplified)
        ctx.fillStyle = getTypeColor(node.type);
        ctx.font = '10px JetBrains Mono';
        ctx.fillText(node.type[0].toUpperCase(), x, y + 4);
      });
      
      time += 0.02;
      animationRef.current = requestAnimationFrame(draw);
    };
    
    draw();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);
  
  return (
    <div className="relative w-full h-[360px] bg-surface-950/50 rounded-xl overflow-hidden">
      <canvas 
        ref={canvasRef} 
        className="w-full h-full"
        style={{ width: '100%', height: '100%' }}
      />
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 flex items-center gap-4 text-xs text-surface-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-quantum-500" />
          <span>Organization</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span>Individual</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span>Account</span>
        </div>
      </div>
    </div>
  );
}

