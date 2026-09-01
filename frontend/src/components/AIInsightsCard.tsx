'use client';

import React from 'react';
import { Sparkles, Brain, Lightbulb, ArrowUpRight } from 'lucide-react';
import { AIInsights } from '../lib/types';
import Link from 'next/link';

interface AIInsightsCardProps {
  insights?: AIInsights | null;
  isLoading?: boolean;
}

export function AIInsightsCard({ insights, isLoading = false }: AIInsightsCardProps) {
  if (isLoading || !insights) {
    return (
      <div className="rounded-xl bg-surface border border-borderDark/80 p-6 flex items-center justify-center h-48 text-xs text-slate-400">
        Synthesizing AI recovery intelligence...
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-indigo-950/40 via-surface to-surface border border-indigo-500/30 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">
              AI Recovery Intelligence & Intent Insights
            </h3>
            <p className="text-xs text-slate-400">
              Aggregated from calibrated GPT-4o-mini & deterministic risk diagnoses
            </p>
          </div>
        </div>

        <Link
          href="/ai-insights"
          className="inline-flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          View AI Analysis <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-4">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Primary Dropoff Pattern
          </span>
          <h4 className="text-sm font-bold text-slate-100 mt-1">
            {insights.top_recovery_reason}
          </h4>
          <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">
            {insights.top_diagnosis_explanation}
          </p>
        </div>

        <div className="rounded-lg bg-slate-900/60 border border-slate-800/80 p-4 flex flex-col justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Estimated Recoverable Opportunity
            </span>
            <div className="mt-2 text-2xl font-bold text-emerald-400">
              ₹{insights.estimated_recoverable_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              High intent checkout concentration: <strong className="text-white">{insights.high_intent_rate}%</strong>
            </p>
          </div>
        </div>

        <div className="rounded-lg bg-indigo-950/30 border border-indigo-800/40 p-4">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-300 uppercase tracking-wider">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            Strategic Recovery Action
          </div>
          <p className="text-xs text-slate-300 mt-2 leading-relaxed">
            {insights.recommended_focus}
          </p>
        </div>
      </div>
    </div>
  );
}
