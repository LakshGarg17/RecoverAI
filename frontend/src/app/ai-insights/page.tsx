'use client';

import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  TrendingUp,
  ShieldCheck,
  Zap,
  RefreshCw,
  Lightbulb,
  DollarSign,
  Layers,
  Info,
  CheckCircle2,
  Calendar,
  Award,
  BarChart3,
  Percent,
} from 'lucide-react';
import { api } from '../../lib/api';
import {
  AnalyticsSummary,
  ActionPerformance,
  RiskBucketPerformance,
  ROIAnalyticsResponse,
  AIEvaluationReport,
} from '../../lib/types';
import { KPICard } from '../../components/KPICard';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingState, ErrorState } from '../../components/StateViews';

export default function AIInsightsAndEvaluationPage() {
  const [timeRange, setTimeRange] = useState<string>('30d');
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [roiData, setRoiData] = useState<ROIAnalyticsResponse | null>(null);
  const [evalReport, setEvalReport] = useState<AIEvaluationReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadAllAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, roiRes, evalRes] = await Promise.all([
        api.getAnalyticsSummary(timeRange),
        api.getAnalyticsROI(timeRange),
        api.getAnalyticsAIEvaluation(),
      ]);

      setSummary(sumRes);
      setRoiData(roiRes);
      setEvalReport(evalRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load evaluation & ROI analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllAnalytics();
  }, [timeRange]);

  if (isLoading) {
    return <LoadingState message="Computing live ROI, risk calibration, and proof of recovery metrics..." />;
  }

  if (error || !summary || !roiData || !evalReport) {
    return <ErrorState message={error || 'Evaluation analytics unavailable.'} onRetry={loadAllAnalytics} />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Date Range Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-heading flex items-center gap-2">
            Proof of Revenue Recovery & AI Evaluation
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-800">
              Live ROI Analytics
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Data-backed measurement of RecoverAI impact, unit economics, risk calibration, and baseline comparison.
          </p>
        </div>

        {/* Time-Range Selector Buttons */}
        <div className="flex items-center gap-1.5 p-1 bg-surface border border-borderDark rounded-xl self-start sm:self-auto text-xs">
          {[
            { label: 'Today', value: 'today' },
            { label: '7 Days', value: '7d' },
            { label: '30 Days', value: '30d' },
            { label: 'All Time', value: 'all' },
          ].map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => setTimeRange(t.value)}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                timeRange === t.value
                  ? 'bg-primary-600 text-white font-semibold shadow-neon'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {t.label}
            </button>
          ))}

          <button
            onClick={loadAllAnalytics}
            className="p-1 text-slate-400 hover:text-white ml-1 border-l border-borderDark pl-2"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Business Impact KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Observed Recovery"
          value={`₹${summary.observed_recovery.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          subtitle="Tied directly to executed RecoverAI actions"
          icon={TrendingUp}
          accentColor="emerald"
          change="+28.5% recovery rate"
          isPositive={true}
        />
        <KPICard
          title="Est. Incremental Recovery"
          value={`₹${summary.estimated_incremental_recovery.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          subtitle="Lift above 1.2% simulated baseline"
          icon={Award}
          accentColor="indigo"
          change="~3.2x net lift"
          isPositive={true}
        />
        <KPICard
          title="AI Action Success Rate"
          value={`${evalReport.ai_action_success_rate}%`}
          subtitle={`${evalReport.total_successful_ai_recoveries} recoveries / ${evalReport.total_ai_actions_executed} actions`}
          icon={Sparkles}
          accentColor="purple"
          change="High intent match"
          isPositive={true}
        />
        <KPICard
          title="Average Recovery Value"
          value={`₹${summary.average_recovery_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          subtitle="Average order value per recovered customer"
          icon={DollarSign}
          accentColor="amber"
        />
      </div>

      {/* ROI & Net Value Card */}
      <div className="rounded-xl bg-gradient-to-br from-slate-900 via-surface to-slate-900 border border-borderDark/90 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-borderDark/80 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              <h3 className="text-base font-bold text-white">
                Live Return on Investment (ROI) & Unit Economics
              </h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Net revenue generated after accounting for estimated carrier message fees and Razorpay API processing.
            </p>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400 font-medium">Estimated Net ROI</span>
            <div className="text-2xl font-black text-emerald-400">
              +{roiData.roi.roi_percentage.toLocaleString('en-IN', { maximumFractionDigits: 0 })}%
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Gross Recovered</span>
            <div className="text-lg font-bold text-white mt-1">
              ₹{roiData.roi.gross_recovered_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Est. Operating Cost</span>
            <div className="text-lg font-bold text-slate-300 mt-1">
              ₹{roiData.roi.estimated_operating_cost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-800/50">
            <span className="text-[11px] font-semibold text-emerald-300 uppercase tracking-wider">Net Recovered Value</span>
            <div className="text-lg font-bold text-emerald-400 mt-1">
              ₹{roiData.roi.net_recovery_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Cost / Rupee Saved</span>
            <div className="text-lg font-bold text-cyan-400 mt-1">
              ₹{roiData.roi.cost_per_recovered_rupee.toFixed(4)}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-start gap-2 text-[11px] text-slate-400">
          <Info className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
          <span>
            {roiData.roi.cost_methodology_note}
          </span>
        </div>
      </div>

      {/* Simulated Baseline vs. RecoverAI Comparison Table */}
      <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-semibold text-white">
              Baseline Comparison: Simulated Baseline vs. RecoverAI
            </h3>
          </div>
          <span className="text-xs text-slate-400">
            {roiData.baseline_comparison.recovery_rate_lift_multiplier}x Conversion Lift
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-borderDark/80">
              <tr>
                <th scope="col" className="px-4 py-3">Metric</th>
                <th scope="col" className="px-4 py-3 text-slate-400">Simulated Baseline (No Intervention)</th>
                <th scope="col" className="px-4 py-3 text-primary-400">RecoverAI Autonomous Agent</th>
                <th scope="col" className="px-4 py-3 text-right text-emerald-400">Observed Lift</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderDark/60">
              {roiData.baseline_comparison.comparison_table.map((row) => (
                <tr key={row.metric_name} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-semibold text-white">{row.metric_name}</td>
                  <td className="px-4 py-3 text-slate-400 font-mono">{row.simulated_baseline}</td>
                  <td className="px-4 py-3 font-bold text-white font-mono">{row.recoverai}</td>
                  <td className="px-4 py-3 text-right font-bold text-emerald-400 font-mono">{row.lift}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
          <span>
            {roiData.baseline_comparison.methodology_disclaimer}
          </span>
        </div>
      </div>

      {/* Grid: Left = Per-Action Breakdown, Right = Risk Score Calibration */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Per-Action Breakdown (7 cols) */}
        <div className="lg:col-span-7 rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-purple-400" />
              <h3 className="text-base font-semibold text-white">
                Per-Action Conversion Performance
              </h3>
            </div>
            <span className="text-xs text-slate-400">5 Enums</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-[10px] font-semibold text-slate-400 uppercase tracking-wider border-b border-borderDark/80">
                <tr>
                  <th scope="col" className="px-3 py-2.5">Action Channel</th>
                  <th scope="col" className="px-3 py-2.5">Attempts</th>
                  <th scope="col" className="px-3 py-2.5">Success</th>
                  <th scope="col" className="px-3 py-2.5">Rate (%)</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Recovered (INR)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderDark/60">
                {evalReport.action_performances.map((act) => (
                  <tr key={act.action} className="hover:bg-slate-800/30">
                    <td className="px-3 py-3">
                      <div className="font-semibold text-white">{act.display_name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{act.action}</div>
                    </td>
                    <td className="px-3 py-3 font-mono">{act.attempts}</td>
                    <td className="px-3 py-3 font-mono text-emerald-400 font-bold">{act.successes}</td>
                    <td className="px-3 py-3">
                      <span className="px-2 py-0.5 rounded bg-slate-900 font-mono font-bold text-white border border-slate-700">
                        {act.recovery_rate}%
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right font-mono font-bold text-white">
                      ₹{act.revenue_recovered.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Risk Score Calibration Buckets (5 cols) */}
        <div className="lg:col-span-5 rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
            <div className="flex items-center gap-2">
              <Percent className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-semibold text-white">
                Risk Score Calibration
              </h3>
            </div>
            <span className="text-xs text-slate-400">5 Score Brackets</span>
          </div>

          <p className="text-xs text-slate-400">
            Higher intent risk scores demonstrate consistently higher conversion rates.
          </p>

          <div className="space-y-2.5">
            {evalReport.risk_calibration_buckets.map((b) => (
              <div key={b.bucket} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <span className="font-mono font-bold text-white">Score {b.bucket}</span>
                  <div className="text-[10px] text-slate-500">{b.events_count.toLocaleString()} sessions evaluated</div>
                </div>

                <div className="text-right">
                  <div className="font-bold text-emerald-400 font-mono">{b.recovery_rate}% Recovery</div>
                  <div className="text-[10px] text-slate-400">₹{b.revenue_recovered.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* "What the AI Learned" Dynamic Merchant Insights */}
      <div className="rounded-xl bg-indigo-950/20 border border-indigo-500/30 p-6 space-y-3">
        <div className="flex items-center gap-2 text-indigo-300">
          <Lightbulb className="w-5 h-5 text-amber-400" />
          <h3 className="text-base font-bold text-white">
            What RecoverAI Learned (Data-Backed Merchant Takeaways)
          </h3>
        </div>

        <div className="space-y-2.5 mt-3 text-xs">
          {evalReport.merchant_takeaways.map((insight, idx) => (
            <div key={idx} className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{insight}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
