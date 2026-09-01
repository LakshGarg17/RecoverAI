export interface ServiceStatus {
  status: string;
  latency_ms?: number | null;
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

export interface DashboardSummary {
  revenue_at_risk: number;
  recovered_revenue: number;
  recovery_rate: number;
  active_recoveries: number;
  blocked_recoveries: number;
  total_events: number;
  currency: string;
}

export interface RecoveryTrendPoint {
  date: string;
  at_risk: number;
  recovered: number;
  attempts: number;
}

export interface FunnelStage {
  stage: string;
  count: number;
  value: number;
  conversion_rate: number;
  description: string;
}

export interface RecoveryFunnel {
  stages: FunnelStage[];
}

export interface ActionDistribution {
  action: string;
  count: number;
  percentage: number;
}

export interface AIInsights {
  top_recovery_reason: string;
  top_diagnosis_category: string;
  top_diagnosis_explanation: string;
  estimated_recoverable_value: number;
  action_distribution: ActionDistribution[];
  high_intent_rate: number;
  recommended_focus: string;
}

export interface RecoveryOpportunity {
  event_id: string;
  customer_id: string;
  amount: number;
  currency: string;
  risk_score: number;
  priority: string;
  ai_action: string;
  guardrail_status: string;
  status: string;
  payment_url?: string | null;
  execution_id?: string | null;
  created_at: string;
}

export interface OpportunitiesResponse {
  items: RecoveryOpportunity[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface GuardrailCheckResult {
  check_name: string;
  status: 'PASSED' | 'FAILED' | 'SKIPPED';
  reason: string;
}

export interface AuditTimelineEvent {
  timestamp: string;
  stage: string;
  title: string;
  description: string;
  status: 'COMPLETED' | 'BLOCKED' | 'PENDING';
}

export interface RecoveryDetail {
  event_id: string;
  customer_id: string;
  cart_value: number;
  currency: string;
  risk_score: number;
  priority: string;
  selected_action: string;
  ai_diagnosis_category: string;
  ai_explanation: string;
  suggested_message: string;
  expected_recovery_value: number;
  guardrail_status: string;
  checks: GuardrailCheckResult[];
  execution: {
    status: string;
    payment_link_id?: string | null;
    payment_url?: string | null;
    provider: string;
    error_code?: string | null;
  };
  recovery: {
    status: string;
    recovered_amount: number;
    payment_id?: string | null;
  };
  timeline: AuditTimelineEvent[];
  event_metadata?: Record<string, any>;
}

export interface RecoveryPolicyConfig {
  policy_version: string;
  max_recovery_attempts: number;
  cooldown_minutes: number;
  minimum_risk_score: number;
  minimum_recovery_probability: number;
  minimum_expected_value: number;
  max_transaction_value: number;
  allow_payment_link: boolean;
  allow_personalized_reminder: boolean;
  allow_checkout_reminder: boolean;
  allow_delayed_follow_up: boolean;
  max_customer_contact_frequency_24h: number;
  high_value_review_threshold: number;
  max_customer_friction: string;
  min_cart_value_for_payment_link: number;
  min_intent_for_payment_link: number;
}

export interface TransactionItem {
  transaction_id: string;
  event_id: string;
  customer_id: string;
  amount: number;
  currency: string;
  payment_link_id?: string;
  payment_id?: string;
  provider: string;
  status: 'RECOVERED' | 'PENDING' | 'FAILED' | string;
  action: string;
  created_at: string;
}

export interface TransactionsResponse {
  items: TransactionItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface AuditLogItem {
  audit_id: string;
  decision_id: string;
  event_id: string;
  customer_id: string;
  requested_action: string;
  final_action: string;
  status: string;
  execution_state: string;
  risk_score: number;
  cart_value?: number;
  policy_version: string;
  checks_passed: number;
  checks_failed: number;
  reason?: string;
  created_at: string;
}

export interface AuditLogsResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface DemoRecoveryCase {
  case_id: string;
  description: string;
  event_data: {
    event_id: string;
    customer_id: string;
    cart_value: number;
    risk_score?: number;
    purchase_status: string;
    session_duration?: number;
    pages_viewed?: number;
    payment_method?: string;
  };
  expected_outcome: {
    guardrail_status: string;
    selected_action: string;
    execution_status: string;
  };
}

export interface RecoveryRunResult {
  event_id: string;
  customer_id?: string;
  risk_score: number;
  priority?: string;
  selected_action: string;
  decision_score?: number;
  guardrail_status: string;
  execution_status: string;
  expected_recovery_value: number;
  payment_link_created: boolean;
  payment_link_id?: string | null;
  payment_url?: string | null;
  execution_id?: string | null;
  reason?: string;
  blocked_reasons?: string[];
}

// Day 9: Dedicated Analytics, ROI & Evaluation Types
export interface AnalyticsSummary {
  revenue_at_risk: number;
  recovery_attempts: number;
  successful_recoveries: number;
  recovered_revenue: number;
  observed_recovery: number;
  estimated_incremental_recovery: number;
  recovery_rate: number;
  average_recovery_value: number;
  active_opportunities: number;
  blocked_by_guardrails: number;
  total_monitored_events: number;
  currency: string;
  time_range: string;
}

export interface ActionPerformance {
  action: string;
  display_name: string;
  attempts: number;
  successes: number;
  recovery_rate: number;
  revenue_recovered: number;
  average_cart_value: number;
}

export interface RiskBucketPerformance {
  bucket: string;
  min_score: number;
  max_score: number;
  events_count: number;
  attempts_count: number;
  recoveries_count: number;
  recovery_rate: number;
  revenue_recovered: number;
}

export interface ROIBreakdown {
  gross_recovered_revenue: number;
  total_recovery_attempts: number;
  estimated_operating_cost: number;
  net_recovery_value: number;
  roi_percentage: number;
  cost_per_recovered_rupee: number;
  currency: string;
  cost_methodology_note: string;
}

export interface MetricComparison {
  metric_name: string;
  simulated_baseline: string;
  recoverai: string;
  lift: string;
}

export interface BaselineComparisonResult {
  comparison_table: MetricComparison[];
  simulated_baseline_revenue: number;
  recoverai_observed_revenue: number;
  estimated_incremental_revenue: number;
  recovery_rate_lift_multiplier: number;
  methodology_disclaimer: string;
}

export interface ROIAnalyticsResponse {
  roi: ROIBreakdown;
  baseline_comparison: BaselineComparisonResult;
}

export interface AIEvaluationReport {
  ai_action_success_rate: number;
  total_ai_actions_executed: number;
  total_successful_ai_recoveries: number;
  total_revenue_influenced: number;
  action_performances: ActionPerformance[];
  risk_calibration_buckets: RiskBucketPerformance[];
  merchant_takeaways: string[];
  evaluation_label_disclaimer: string;
}

