'use client';

import { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  Filter, 
  Search, 
  Calendar,
  DollarSign,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Target,
  ChevronRight,
  Building,
  User,
  Tag
} from 'lucide-react';

interface Proposal {
  id: string;
  proposal_number: string;
  proposal_type: string;
  client_name: string;
  client_industry: string;
  client_country: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  solution_areas: string[];
  due_date: string;
  estimated_deal_value: number;
  currency: string;
  lead_owner: string;
  win_probability: number;
  created_at: string;
}

interface DashboardStats {
  active_proposals: number;
  due_this_week: number;
  win_rate: number;
  total_won_value: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

// Mock data for demonstration
const mockProposals: Proposal[] = [
  {
    id: '1',
    proposal_number: 'RFP-202501-0001',
    proposal_type: 'rfp',
    client_name: 'DBS Bank',
    client_industry: 'Banking',
    client_country: 'Singapore',
    title: 'AML Transaction Monitoring Solution',
    description: 'End-to-end AML transaction monitoring with entity resolution capabilities',
    status: 'in_progress',
    priority: 'high',
    solution_areas: ['AML', 'Transaction Monitoring', 'Entity Resolution'],
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    estimated_deal_value: 2500000,
    currency: 'USD',
    lead_owner: 'Alex Chen',
    win_probability: 0.65,
    created_at: new Date().toISOString()
  },
  {
    id: '2',
    proposal_number: 'RFP-202501-0002',
    proposal_type: 'rfp',
    client_name: 'UOB',
    client_industry: 'Banking',
    client_country: 'Singapore',
    title: 'Fraud Detection Platform',
    description: 'Real-time fraud detection with network analytics',
    status: 'review',
    priority: 'critical',
    solution_areas: ['Fraud Detection', 'Network Analytics', 'Real-time Monitoring'],
    due_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
    estimated_deal_value: 1800000,
    currency: 'USD',
    lead_owner: 'Sarah Wong',
    win_probability: 0.72,
    created_at: new Date().toISOString()
  },
  {
    id: '3',
    proposal_number: 'RFI-202501-0001',
    proposal_type: 'rfi',
    client_name: 'OCBC',
    client_industry: 'Banking',
    client_country: 'Singapore',
    title: 'KYC/CDD Enhancement Solution',
    description: 'Information request for KYC customer due diligence platform',
    status: 'draft',
    priority: 'medium',
    solution_areas: ['KYC', 'CDD', 'Entity Resolution'],
    due_date: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString(),
    estimated_deal_value: 1200000,
    currency: 'USD',
    lead_owner: 'Alex Chen',
    win_probability: 0.50,
    created_at: new Date().toISOString()
  },
  {
    id: '4',
    proposal_number: 'RFP-202412-0001',
    proposal_type: 'rfp',
    client_name: 'Standard Chartered',
    client_industry: 'Banking',
    client_country: 'Singapore',
    title: 'Enterprise Sanctions Screening',
    description: 'Global sanctions screening with PEP and adverse media',
    status: 'won',
    priority: 'high',
    solution_areas: ['Sanctions Screening', 'PEP', 'Risk Management'],
    due_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    estimated_deal_value: 3200000,
    currency: 'USD',
    lead_owner: 'Alex Chen',
    win_probability: 1.00,
    created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: '5',
    proposal_number: 'RFP-202411-0001',
    proposal_type: 'rfp',
    client_name: 'MUFG',
    client_industry: 'Banking',
    client_country: 'Singapore',
    title: 'Trade Finance Compliance',
    description: 'Trade finance transaction monitoring and compliance',
    status: 'lost',
    priority: 'high',
    solution_areas: ['Trade Finance', 'Compliance', 'Transaction Monitoring'],
    due_date: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
    estimated_deal_value: 1500000,
    currency: 'USD',
    lead_owner: 'Sarah Wong',
    win_probability: 0.00,
    created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString()
  }
];

const mockDashboard: DashboardStats = {
  active_proposals: 3,
  due_this_week: 1,
  win_rate: 50,
  total_won_value: 3200000,
  by_status: {
    draft: 1,
    in_progress: 1,
    review: 1,
    submitted: 0,
    won: 1,
    lost: 1,
    no_bid: 0,
    withdrawn: 0
  },
  by_type: {
    rfp: 4,
    rfi: 1,
    rfq: 0,
    eoi: 0
  }
};

const statusColors: Record<string, { bg: string; text: string; dot: string }> = {
  draft: { bg: 'bg-gray-500/10', text: 'text-gray-400', dot: 'bg-gray-400' },
  in_progress: { bg: 'bg-blue-500/10', text: 'text-blue-400', dot: 'bg-blue-400' },
  review: { bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-400' },
  submitted: { bg: 'bg-purple-500/10', text: 'text-purple-400', dot: 'bg-purple-400' },
  won: { bg: 'bg-green-500/10', text: 'text-green-400', dot: 'bg-green-400' },
  lost: { bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-400' },
  no_bid: { bg: 'bg-gray-500/10', text: 'text-gray-400', dot: 'bg-gray-400' },
  withdrawn: { bg: 'bg-gray-500/10', text: 'text-gray-400', dot: 'bg-gray-400' }
};

const priorityColors: Record<string, { bg: string; text: string }> = {
  low: { bg: 'bg-gray-500/10', text: 'text-gray-400' },
  medium: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
  high: { bg: 'bg-orange-500/10', text: 'text-orange-400' },
  critical: { bg: 'bg-red-500/10', text: 'text-red-400' }
};

function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

function getDaysUntilDue(dueDate: string): number {
  const due = new Date(dueDate);
  const now = new Date();
  return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

export default function RFPPanel() {
  const [proposals, setProposals] = useState<Proposal[]>(mockProposals);
  const [dashboard, setDashboard] = useState<DashboardStats>(mockDashboard);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);

  const filteredProposals = proposals.filter(p => {
    const matchesSearch = 
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.client_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.proposal_number.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
    const matchesType = typeFilter === 'all' || p.proposal_type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">RFP & RFI Management</h1>
          <p className="text-surface-400 mt-1">Track and manage proposals throughout their lifecycle</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-quantum-500 to-cyan-500 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-quantum-500/25 transition-all">
          <Plus className="w-5 h-5" />
          New Proposal
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-800/50 backdrop-blur-sm rounded-2xl border border-surface-700/50 p-5">
          <div className="flex items-center justify-between">
            <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center">
              <FileText className="w-6 h-6 text-blue-400" />
            </div>
            <span className="text-xs font-medium text-surface-400">ACTIVE</span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-display font-bold text-white">{dashboard.active_proposals}</span>
            <p className="text-sm text-surface-400 mt-1">Open Proposals</p>
          </div>
        </div>

        <div className="bg-surface-800/50 backdrop-blur-sm rounded-2xl border border-surface-700/50 p-5">
          <div className="flex items-center justify-between">
            <div className="w-12 h-12 bg-amber-500/10 rounded-xl flex items-center justify-center">
              <Clock className="w-6 h-6 text-amber-400" />
            </div>
            <span className="text-xs font-medium text-amber-400">URGENT</span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-display font-bold text-white">{dashboard.due_this_week}</span>
            <p className="text-sm text-surface-400 mt-1">Due This Week</p>
          </div>
        </div>

        <div className="bg-surface-800/50 backdrop-blur-sm rounded-2xl border border-surface-700/50 p-5">
          <div className="flex items-center justify-between">
            <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-400" />
            </div>
            <span className="text-xs font-medium text-surface-400">WIN RATE</span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-display font-bold text-white">{dashboard.win_rate}%</span>
            <p className="text-sm text-surface-400 mt-1">Last 12 Months</p>
          </div>
        </div>

        <div className="bg-surface-800/50 backdrop-blur-sm rounded-2xl border border-surface-700/50 p-5">
          <div className="flex items-center justify-between">
            <div className="w-12 h-12 bg-quantum-500/10 rounded-xl flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-quantum-400" />
            </div>
            <span className="text-xs font-medium text-surface-400">REVENUE</span>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-display font-bold text-white">{formatCurrency(dashboard.total_won_value)}</span>
            <p className="text-sm text-surface-400 mt-1">Won Value</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-500" />
          <input
            type="text"
            placeholder="Search proposals..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-surface-800/50 border border-surface-700/50 rounded-xl text-white placeholder-surface-500 focus:outline-none focus:border-quantum-500/50 transition-colors"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2.5 bg-surface-800/50 border border-surface-700/50 rounded-xl text-white focus:outline-none focus:border-quantum-500/50 transition-colors"
        >
          <option value="all">All Status</option>
          <option value="draft">Draft</option>
          <option value="in_progress">In Progress</option>
          <option value="review">Under Review</option>
          <option value="submitted">Submitted</option>
          <option value="won">Won</option>
          <option value="lost">Lost</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2.5 bg-surface-800/50 border border-surface-700/50 rounded-xl text-white focus:outline-none focus:border-quantum-500/50 transition-colors"
        >
          <option value="all">All Types</option>
          <option value="rfp">RFP</option>
          <option value="rfi">RFI</option>
          <option value="rfq">RFQ</option>
        </select>
      </div>

      {/* Proposals Grid */}
      <div className="grid gap-4">
        {filteredProposals.map((proposal) => {
          const daysUntilDue = getDaysUntilDue(proposal.due_date);
          const status = statusColors[proposal.status] || statusColors.draft;
          const priority = priorityColors[proposal.priority] || priorityColors.medium;
          const isOverdue = daysUntilDue < 0 && !['won', 'lost', 'withdrawn'].includes(proposal.status);
          
          return (
            <div
              key={proposal.id}
              onClick={() => setSelectedProposal(proposal)}
              className="bg-surface-800/50 backdrop-blur-sm rounded-2xl border border-surface-700/50 p-5 hover:border-quantum-500/30 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs font-mono text-surface-500">{proposal.proposal_number}</span>
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.bg} ${status.text}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`}></span>
                      {proposal.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${priority.bg} ${priority.text}`}>
                      {proposal.priority.toUpperCase()}
                    </span>
                    <span className="px-2.5 py-1 bg-surface-700/50 rounded-full text-xs font-medium text-surface-400 uppercase">
                      {proposal.proposal_type}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-white group-hover:text-quantum-400 transition-colors">
                    {proposal.title}
                  </h3>
                  <p className="text-sm text-surface-400 mt-1 line-clamp-1">{proposal.description}</p>
                  
                  <div className="flex items-center gap-6 mt-4">
                    <div className="flex items-center gap-2 text-sm text-surface-400">
                      <Building className="w-4 h-4" />
                      {proposal.client_name}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-surface-400">
                      <User className="w-4 h-4" />
                      {proposal.lead_owner}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-surface-400">
                      <DollarSign className="w-4 h-4" />
                      {formatCurrency(proposal.estimated_deal_value, proposal.currency)}
                    </div>
                    <div className={`flex items-center gap-2 text-sm ${isOverdue ? 'text-red-400' : 'text-surface-400'}`}>
                      <Calendar className="w-4 h-4" />
                      {isOverdue ? (
                        <span className="font-medium">Overdue by {Math.abs(daysUntilDue)} days</span>
                      ) : (
                        <span>{formatDate(proposal.due_date)} ({daysUntilDue} days)</span>
                      )}
                    </div>
                  </div>

                  {/* Solution Areas */}
                  <div className="flex items-center gap-2 mt-3">
                    <Tag className="w-4 h-4 text-surface-500" />
                    {proposal.solution_areas.slice(0, 3).map((area, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-surface-700/50 rounded text-xs text-surface-400">
                        {area}
                      </span>
                    ))}
                    {proposal.solution_areas.length > 3 && (
                      <span className="text-xs text-surface-500">+{proposal.solution_areas.length - 3} more</span>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-3">
                  {/* Win Probability Gauge */}
                  <div className="text-right">
                    <div className="text-xs text-surface-500 mb-1">Win Probability</div>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-surface-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all ${
                            proposal.win_probability >= 0.7 ? 'bg-green-500' :
                            proposal.win_probability >= 0.4 ? 'bg-amber-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${proposal.win_probability * 100}%` }}
                        />
                      </div>
                      <span className={`text-sm font-bold ${
                        proposal.win_probability >= 0.7 ? 'text-green-400' :
                        proposal.win_probability >= 0.4 ? 'text-amber-400' :
                        'text-red-400'
                      }`}>
                        {Math.round(proposal.win_probability * 100)}%
                      </span>
                    </div>
                  </div>
                  
                  <ChevronRight className="w-5 h-5 text-surface-500 group-hover:text-quantum-400 transition-colors" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredProposals.length === 0 && (
        <div className="text-center py-12 bg-surface-800/50 rounded-2xl border border-surface-700/50">
          <FileText className="w-12 h-12 text-surface-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No proposals found</h3>
          <p className="text-surface-400 mb-4">Try adjusting your filters or create a new proposal</p>
          <button className="flex items-center gap-2 px-4 py-2 bg-quantum-500/10 text-quantum-400 rounded-xl font-medium hover:bg-quantum-500/20 transition-all mx-auto">
            <Plus className="w-4 h-4" />
            Create Proposal
          </button>
        </div>
      )}

      {/* Pipeline Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Status Distribution */}
        <div className="bg-surface-800/50 backdrop-blur-sm rounded-2xl border border-surface-700/50 p-5">
          <h3 className="text-lg font-semibold text-white mb-4">Pipeline by Status</h3>
          <div className="space-y-3">
            {Object.entries(dashboard.by_status).filter(([_, count]) => count > 0).map(([status, count]) => {
              const colors = statusColors[status] || statusColors.draft;
              const total = Object.values(dashboard.by_status).reduce((a, b) => a + b, 0);
              const percentage = total > 0 ? (count / total) * 100 : 0;
              
              return (
                <div key={status} className="flex items-center gap-3">
                  <div className="w-24 text-sm text-surface-400 capitalize">{status.replace('_', ' ')}</div>
                  <div className="flex-1 h-2 bg-surface-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${colors.dot}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-sm font-medium text-white">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Type Distribution */}
        <div className="bg-surface-800/50 backdrop-blur-sm rounded-2xl border border-surface-700/50 p-5">
          <h3 className="text-lg font-semibold text-white mb-4">Proposals by Type</h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(dashboard.by_type).map(([type, count]) => (
              <div key={type} className="bg-surface-700/30 rounded-xl p-4 text-center">
                <span className="text-2xl font-display font-bold text-white">{count}</span>
                <p className="text-sm text-surface-400 mt-1 uppercase">{type}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

