/**
 * API Client for FTex Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  private buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    return url.toString();
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options;
    const url = this.buildUrl(endpoint, params);

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Entities
  async getEntities(params?: {
    entity_type?: string;
    risk_score_min?: number;
    risk_score_max?: number;
    is_sanctioned?: boolean;
    is_pep?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }) {
    return this.request('/entities/', { params });
  }

  async getEntity(id: string) {
    return this.request(`/entities/${id}`);
  }

  async getEntityRelationships(id: string, depth = 2) {
    return this.request(`/entities/${id}/relationships`, { params: { depth } });
  }

  // Transactions
  async getTransactions(params?: {
    transaction_type?: string;
    min_amount?: number;
    max_amount?: number;
    is_flagged?: boolean;
    page?: number;
    page_size?: number;
  }) {
    return this.request('/transactions/', { params });
  }

  async getTransactionStats(days = 30) {
    return this.request('/transactions/stats', { params: { days } });
  }

  async flagTransaction(id: string, reason: string) {
    return this.request(`/transactions/${id}/flag`, {
      method: 'POST',
      params: { reason },
    });
  }

  // Alerts
  async getAlerts(params?: {
    status?: string;
    severity?: string;
    category?: string;
    page?: number;
    page_size?: number;
  }) {
    return this.request('/alerts/', { params });
  }

  async getAlertDashboard() {
    return this.request('/alerts/dashboard');
  }

  async assignAlert(id: string, assignedTo: string) {
    return this.request(`/alerts/${id}/assign`, {
      method: 'POST',
      params: { assigned_to: assignedTo },
    });
  }

  async resolveAlert(id: string, resolution: string, notes?: string) {
    return this.request(`/alerts/${id}/resolve`, {
      method: 'POST',
      params: { resolution, notes },
    });
  }

  // Cases
  async getCases(params?: {
    status?: string;
    case_type?: string;
    assigned_to?: string;
    page?: number;
    page_size?: number;
  }) {
    return this.request('/cases/', { params });
  }

  async getCaseDashboard() {
    return this.request('/cases/dashboard');
  }

  // Analytics
  async getRiskDistribution() {
    return this.request('/analytics/risk-distribution');
  }

  async getTransactionTrends(days = 30) {
    return this.request('/analytics/transaction-trends', { params: { days } });
  }

  async getHighRiskEntities(limit = 20) {
    return this.request('/analytics/high-risk-entities', { params: { limit } });
  }

  // Graph
  async getEntityNetwork(entityId: string, depth = 2, limit = 100) {
    return this.request(`/graph/entity/${entityId}/network`, {
      params: { depth, limit },
    });
  }

  async findShortestPath(sourceId: string, targetId: string) {
    return this.request('/graph/shortest-path', {
      params: { source_id: sourceId, target_id: targetId },
    });
  }

  // Search
  async searchGlobal(query: string, page = 1, pageSize = 10) {
    return this.request('/search/global', {
      params: { q: query, page, page_size: pageSize },
    });
  }

  async screenNames(names: string[], threshold = 0.8) {
    return this.request('/search/screening', {
      method: 'POST',
      body: JSON.stringify({ names, threshold }),
    });
  }

  // RFP/RFI Management
  async getProposals(params?: {
    proposal_type?: string;
    status?: string;
    priority?: string;
    client_name?: string;
    lead_owner?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) {
    return this.request('/rfp/', { params });
  }

  async getProposalDashboard() {
    return this.request('/rfp/dashboard');
  }

  async getProposal(id: string) {
    return this.request(`/rfp/${id}`);
  }

  async createProposal(data: {
    proposal_type: string;
    client_name: string;
    title: string;
    description?: string;
    priority?: string;
    solution_areas?: string[];
    due_date?: string;
    estimated_deal_value?: number;
    lead_owner?: string;
  }) {
    return this.request('/rfp/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProposal(id: string, data: Record<string, unknown>) {
    return this.request(`/rfp/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async submitProposal(id: string) {
    return this.request(`/rfp/${id}/submit`, { method: 'POST' });
  }

  async recordProposalOutcome(id: string, outcome: 'won' | 'lost', reason?: string) {
    return this.request(`/rfp/${id}/outcome`, {
      method: 'POST',
      params: { outcome, reason },
    });
  }

  async getProposalSections(proposalId: string) {
    return this.request(`/rfp/${proposalId}/sections`);
  }

  async createProposalSection(proposalId: string, data: {
    title: string;
    section_number?: string;
    question?: string;
    category?: string;
    is_mandatory?: boolean;
    assigned_to?: string;
  }) {
    return this.request(`/rfp/${proposalId}/sections`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProposalSection(proposalId: string, sectionId: string, data: {
    response?: string;
    response_status?: string;
    assigned_to?: string;
  }) {
    return this.request(`/rfp/${proposalId}/sections/${sectionId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getContentLibrary(params?: {
    category?: string;
    solution_area?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) {
    return this.request('/rfp/library/content', { params });
  }

  async getContentItem(id: string) {
    return this.request(`/rfp/library/content/${id}`);
  }

  async createContentItem(data: {
    title: string;
    content: string;
    category?: string;
    solution_area?: string;
    tags?: string[];
    keywords?: string[];
  }) {
    return this.request('/rfp/library/content', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getWinLossAnalytics(months = 12) {
    return this.request('/rfp/analytics/win-loss', { params: { months } });
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;

