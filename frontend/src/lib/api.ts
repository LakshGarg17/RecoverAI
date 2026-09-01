import {
  HealthResponse,
  DashboardSummary,
  RecoveryTrendPoint,
  RecoveryFunnel,
  AIInsights,
  OpportunitiesResponse,
  RecoveryDetail,
  RecoveryPolicyConfig,
  TransactionsResponse,
  AuditLogsResponse,
  DemoRecoveryCase,
  RecoveryRunResult,
} from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  }

  private async post<T>(path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  }

  async checkHealth(): Promise<{ data: HealthResponse | null; latencyMs: number; error?: string }> {
    const start = performance.now();
    try {
      const res = await fetch(`${this.baseUrl}/api/health`, {
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
      });
      const latencyMs = Math.round(performance.now() - start);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const data: HealthResponse = await res.json();
      return { data, latencyMs };
    } catch (err: any) {
      const latencyMs = Math.round(performance.now() - start);
      return {
        data: null,
        latencyMs,
        error: err.message || 'Backend connection failed',
      };
    }
  }

  async getDashboardSummary(): Promise<DashboardSummary> {
    return this.get<DashboardSummary>('/api/dashboard/summary');
  }

  async getRecoveryTrend(days: number = 14): Promise<RecoveryTrendPoint[]> {
    return this.get<RecoveryTrendPoint[]>(`/api/dashboard/recovery-trend?days=${days}`);
  }

  async getRecoveryFunnel(): Promise<RecoveryFunnel> {
    return this.get<RecoveryFunnel>('/api/dashboard/funnel');
  }

  async getAIInsights(): Promise<AIInsights> {
    return this.get<AIInsights>('/api/dashboard/ai-insights');
  }

  async getOpportunities(params: {
    page?: number;
    limit?: number;
    status?: string;
    risk?: string;
    action?: string;
    search?: string;
  } = {}): Promise<OpportunitiesResponse> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.limit) query.set('limit', params.limit.toString());
    if (params.status && params.status !== 'ALL') query.set('status', params.status);
    if (params.risk && params.risk !== 'ALL') query.set('risk', params.risk);
    if (params.action && params.action !== 'ALL') query.set('action', params.action);
    if (params.search) query.set('search', params.search);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.get<OpportunitiesResponse>(`/api/recovery/opportunities${queryString}`);
  }

  async getRecoveryDetail(eventId: string): Promise<RecoveryDetail> {
    return this.get<RecoveryDetail>(`/api/recovery/detail/${eventId}`);
  }

  async getDemoCases(): Promise<DemoRecoveryCase[]> {
    return this.get<DemoRecoveryCase[]>('/api/recovery/demo-cases');
  }

  async runRecovery(payload: {
    event_id?: string;
    event_data?: any;
    current_purchase_status?: string;
    policy_overrides?: any;
  }, idempotencyKey?: string): Promise<RecoveryRunResult> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    return this.post<RecoveryRunResult>('/api/recovery/run', payload, headers);
  }

  async getGuardrailsPolicy(): Promise<RecoveryPolicyConfig> {
    return this.get<RecoveryPolicyConfig>('/api/guardrails/policy');
  }

  async getTransactions(params: {
    page?: number;
    limit?: number;
    status?: string;
    search?: string;
  } = {}): Promise<TransactionsResponse> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.limit) query.set('limit', params.limit.toString());
    if (params.status && params.status !== 'ALL') query.set('status', params.status);
    if (params.search) query.set('search', params.search);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.get<TransactionsResponse>(`/api/transactions${queryString}`);
  }

  async getAuditLogs(params: {
    page?: number;
    limit?: number;
    status?: string;
    action?: string;
    search?: string;
  } = {}): Promise<AuditLogsResponse> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.limit) query.set('limit', params.limit.toString());
    if (params.status && params.status !== 'ALL') query.set('status', params.status);
    if (params.action && params.action !== 'ALL') query.set('action', params.action);
    if (params.search) query.set('search', params.search);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.get<AuditLogsResponse>(`/api/audit/logs${queryString}`);
  }
}

export const api = new ApiClient(API_URL);
