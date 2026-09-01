'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  DollarSign,
  TrendingUp,
  ShieldCheck,
  Zap,
  ArrowRight,
  AlertOctagon,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import {
  DashboardSummary,
  RecoveryTrendPoint,
  RecoveryFunnel as RecoveryFunnelType,
  AIInsights,
  RecoveryOpportunity,
} from '../lib/types';
import { KPICard } from '../components/KPICard';
import { RecoveryMetricsChart } from '../components/RecoveryMetricsChart';
import { RecoveryFunnel } from '../components/RecoveryFunnel';
import { AIInsightsCard } from '../components/AIInsightsCard';
import { AIDecisionDistributionChart } from '../components/AIDecisionDistributionChart';
import { RecoveryTable } from '../components/RecoveryTable';
import { LoadingState, ErrorState } from '../components/StateViews';

export default function DashboardOverviewPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trend, setTrend] = useState<RecoveryTrendPoint[]>([]);
  const [funnel, setFunnel] = useState<RecoveryFunnelType | null>(null);
  const [insights, setInsights] = useState<AIInsights | null>(null);
  const [opportunities, setOpportunities] = useState<RecoveryOpportunity[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, trendRes, funnelRes, insightsRes, oppRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getRecoveryTrend(14),
        api.getRecoveryFunnel(),
        api.getAIInsights(),
        api.getOpportunities({ limit: 6 }),
      ]);

      setSummary(sumRes);
      setTrend(trendRes);
      setFunnel(funnelRes);
      setInsights(insightsRes);
      setOpportunities(oppRes.items);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to RecoverAI backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (isLoading) {
    return <LoadingState message="Aggregating autonomous recovery telemetry..." />;
  }

  if (error && !summary) {
    return <ErrorState message={error} onRetry={loadDashboardData} />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-heading flex items-center gap-2">
            Merchant Recovery Operations
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary-950 text-primary-300 border border-primary-800">
              Live Telemetry
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time intent diagnosis, bounded guardrail enforcement, and Razorpay Test Mode execution.
          </p>
        </div>

        <button
          onClick={loadDashboardData}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-surface hover:bg-slate-800 border border-borderDark rounded-xl transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Analytics
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Revenue At Risk"
          value={`₹${(summary?.revenue_at_risk || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          subtitle={`${summary?.total_events.toLocaleString() || '25,000'} total monitored checkout sessions`}
          icon={DollarSign}
          accentColor="amber"
          change="+12.4% vs last week"
          isPositive={false}
        />
        <KPICard
          title="Recovered Revenue"
          value={`₹${(summary?.recovered_revenue || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          subtitle="Reconciled via Razorpay Test Mode & dunning"
          icon={TrendingUp}
          accentColor="emerald"
          change="+28.6% recovered"
          isPositive={true}
        />
        <KPICard
          title="Recovery Rate"
          value={`${summary?.recovery_rate || 0}%`}
          subtitle="Percentage of recoverable cart value saved"
          icon={ShieldCheck}
          accentColor="indigo"
          change="+4.2% lift"
          isPositive={true}
        />
        <KPICard
          title="Active vs Blocked"
          value={`${summary?.active_recoveries || 0} / ${summary?.blocked_recoveries || 0}`}
          subtitle="Active interventions vs guardrail protected"
          icon={Zap}
          accentColor="purple"
        />
      </div>

      {/* Charts Row: Trend & Action Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecoveryMetricsChart data={trend} />
        </div>
        <div>
          <AIDecisionDistributionChart distribution={insights?.action_distribution} />
        </div>
      </div>

      {/* 5-Stage Recovery Funnel */}
      {funnel && <RecoveryFunnel stages={funnel.stages} />}

      {/* AI Recovery Insights Highlight */}
      <AIInsightsCard insights={insights} />

      {/* Recent Recovery Opportunities Preview */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">
              High-Priority Recovery Opportunities
            </h3>
            <p className="text-xs text-slate-400">
              Recent abandoned checkout sessions diagnosed and ready for intervention.
            </p>
          </div>
          <Link
            href="/recovery"
            className="inline-flex items-center gap-1 text-xs font-semibold text-primary-400 hover:text-primary-300 transition-colors"
          >
            View All ({summary?.total_events.toLocaleString() || '1,000+'}) <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <RecoveryTable opportunities={opportunities} limit={6} />
      </div>
    </div>
  );
}
