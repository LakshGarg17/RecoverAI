export interface ServiceStatus {
  status: string;
  latency_ms?: number;
  details?: Record<string, any>;
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  version: string;
  timestamp: string;
  environment: string;
  services: {
    backend?: ServiceStatus;
    database?: ServiceStatus;
    razorpay?: ServiceStatus;
    openai?: ServiceStatus;
    [key: string]: ServiceStatus | undefined;
  };
}

export interface PaymentOrderPayload {
  amount: number;
  currency?: string;
  receipt?: string;
  notes?: Record<string, string>;
}

export interface PaymentOrderResponse {
  id: string;
  entity: string;
  amount: number;
  amount_paid: number;
  amount_due: number;
  currency: string;
  receipt?: string;
  status: string;
}

export interface AIAnalysisPayload {
  customer_name: string;
  overdue_days: number;
  amount: number;
  currency?: string;
  previous_communications?: string[];
}

export interface AIAnalysisResponse {
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  recommended_action: string;
  suggested_channel: string;
  personalized_draft: string;
  confidence_score: number;
}
