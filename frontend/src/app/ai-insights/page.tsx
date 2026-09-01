'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, Brain, Layers, RefreshCw, Lightbulb, Target } from 'lucide-react';
import { api } from '../../lib/api';
import { AIInsights } from '../../lib/types';
import { AIDecisionDistributionChart } from '../../components/AIDecisionDistributionChart';
import { LoadingState, ErrorState } from '../../components/StateViews';

export default function AIInsightsPage() {
  const [insights, setInsights] = useState<AIInsights | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadInsights = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getAIInsights();
      setInsights(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load AI recovery intelligence.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, []);

  if (isLoading) {
    return <LoadingState message="Synthesizing AI diagnoses across historical dropoffs..." />;
  }

  if (error || !insights) {
    return <ErrorState message={error || 'AI intelligence unavailable.'} onRetry={loadInsights} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-heading flex items-center gap-2">
            AI Recovery Intelligence & Diagnostics
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-800">
              GPT-4o-mini Calibrated
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Aggregated diagnostics, friction classifications, and autonomous recovery action distributions.
          </p>
        </div>

        <button
          onClick={loadInsights}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-surface hover:bg-slate-800 border border-borderDark rounded-xl transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Intelligence
        </button>
      </div>

      {/* Primary Diagnostic Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-surface border border-borderDark/80 p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-400 uppercase tracking-wider">
            <Brain className="w-4 h-4" /> Top Loss Classification
          </div>
          <div className="text-lg font-bold text-white">{insights.top_diagnosis_category}</div>
          <p className="text-xs text-slate-400 leading-relaxed">{insights.top_diagnosis_explanation}</p>
        </div>

        <div className="rounded-xl bg-surface border border-borderDark/80 p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider">
            <Target className="w-4 h-4" /> Recoverable Revenue Potential
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            ₹{insights.estimated_recoverable_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            High intent cart concentration: <strong className="text-white">{insights.high_intent_rate}%</strong>
          </p>
        </div>

        <div className="rounded-xl bg-indigo-950/30 border border-indigo-800/50 p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-300 uppercase tracking-wider">
            <Lightbulb className="w-4 h-4 text-amber-400" /> Strategic Action Focus
          </div>
          <div className="text-sm font-bold text-white">{insights.top_recovery_reason}</div>
          <p className="text-xs text-slate-300 leading-relaxed">{insights.recommended_focus}</p>
        </div>
      </div>

      {/* Decision Engine Breakdown Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <AIDecisionDistributionChart distribution={insights.action_distribution} />
        </div>

        {/* Clinical Heuristics Card */}
        <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-semibold text-white">
                Decision Engine Action Selection Policy
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              How RecoverAI maps AI diagnosis & expected value to deterministic actions.
            </p>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-purple-400 mt-1.5" />
                <div>
                  <strong className="text-white block">PAYMENT_LINK (Razorpay Test Mode)</strong>
                  <p className="text-slate-400 mt-0.5">High-value carts (&gt;₹1,500) with technical failure signals. Dispatches direct checkout link.</p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-blue-400 mt-1.5" />
                <div>
                  <strong className="text-white block">PERSONALIZED_REMINDER</strong>
                  <p className="text-slate-400 mt-0.5">High-intent repeat buyers with previous transactions. Sends context-aware empathetic draft.</p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-cyan-400 mt-1.5" />
                <div>
                  <strong className="text-white block">CHECKOUT_REMINDER</strong>
                  <p className="text-slate-400 mt-0.5">Standard single-item dropoffs with low friction tolerance.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
