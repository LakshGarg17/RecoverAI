import { HealthResponse, PaymentOrderPayload, PaymentOrderResponse, AIAnalysisPayload, AIAnalysisResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
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
        error: err.message || 'Failed to connect to backend server',
      };
    }
  }

  async createPaymentOrder(payload: PaymentOrderPayload): Promise<PaymentOrderResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/payments/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create payment order (${res.status})`);
    }

    return res.json();
  }

  async analyzeInvoice(payload: AIAnalysisPayload): Promise<AIAnalysisResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/ai/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `AI analysis failed (${res.status})`);
    }

    return res.json();
  }
}

export const api = new ApiClient(API_URL);
