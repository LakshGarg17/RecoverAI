'use client';

import React, { useState, useEffect } from 'react';
import { ShieldCheck, Lock, AlertOctagon, CheckCircle2, RefreshCw, Settings2, Info } from 'lucide-react';
import { api } from '../../lib/api';
import { RecoveryPolicyConfig } from '../../lib/types';
import { LoadingState, ErrorState } from '../../components/StateViews';

export default function GuardrailsPolicyPage() {
  const [policy, setPolicy] = useState<RecoveryPolicyConfig | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadPolicy = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getGuardrailsPolicy();
      setPolicy(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load merchant recovery policy.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPolicy();
  }, []);

  if (isLoading) {
    return <LoadingState message="Loading merchant safety policy and guardrail configurations..." />;
  }

  if (error || !policy) {
    return <ErrorState message={error || 'Failed to read recovery policy.'} onRetry={loadPolicy} />;
  }

  const permissions = [
    { name: 'Razorpay Direct Payment Links', key: 'allow_payment_link', enabled: policy.allow_payment_link, desc: 'Generates instant Razorpay Test Mode checkout URLs for high-intent checkouts.' },
    { name: 'Personalized AI Messages', key: 'allow_personalized_reminder', enabled: policy.allow_personalized_reminder, desc: 'Enables empathetic LLM-crafted dunning drafts for repeat and VIP buyers.' },
    { name: 'Standard Checkout Reminders', key: 'allow_checkout_reminder', enabled: policy.allow_checkout_reminder, desc: 'Dispatches lightweight cart reminders for low-friction shoppers.' },
    { name: 'Delayed Follow-up Tasks', key: 'allow_delayed_follow_up', enabled: policy.allow_delayed_follow_up, desc: 'Schedules staged reminders after the quiet cooldown period.' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-heading flex items-center gap-2">
            Guardrails & Merchant Recovery Policy
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
              Policy {policy.policy_version}
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic risk boundaries, transaction caps, cooldown rules, and customer contact frequency limits.
          </p>
        </div>

        <button
          onClick={loadPolicy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-surface hover:bg-slate-800 border border-borderDark rounded-xl transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Policy
        </button>
      </div>

      {/* Read-Only Status Banner */}
      <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 flex items-start gap-3 text-xs text-indigo-200">
        <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-white block">Active Merchant Guardrail Enforcements</strong>
          Policy parameters are managed via backend policy configuration (<code className="text-indigo-300 font-mono">backend/config/recovery_policy.py</code>). These thresholds are strictly evaluated in memory before every Razorpay Test Mode execution.
        </div>
      </div>

      {/* Numerical Thresholds Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-surface border border-borderDark/80 p-5 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Risk & Probability Thresholds
          </span>
          <div className="pt-2 space-y-2.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Min Risk Score:</span>
              <span className="font-bold text-white font-mono">{policy.minimum_risk_score} / 100</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Min Recovery Probability:</span>
              <span className="font-bold text-emerald-400 font-mono">{(policy.minimum_recovery_probability * 100).toFixed(0)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Min Expected Value:</span>
              <span className="font-bold text-white font-mono">₹{policy.minimum_expected_value.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-surface border border-borderDark/80 p-5 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Transaction & Value Caps
          </span>
          <div className="pt-2 space-y-2.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Max Auto Recovery Value:</span>
              <span className="font-bold text-white font-mono">₹{policy.max_transaction_value.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">High-Value Review Threshold:</span>
              <span className="font-bold text-amber-400 font-mono">₹{policy.high_value_review_threshold.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Min Cart for Payment Link:</span>
              <span className="font-bold text-white font-mono">₹{policy.min_cart_value_for_payment_link}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-surface border border-borderDark/80 p-5 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Anti-Spam & Cooldown Rules
          </span>
          <div className="pt-2 space-y-2.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Max Attempts / Event:</span>
              <span className="font-bold text-white font-mono">{policy.max_recovery_attempts} attempts</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Cooldown Quiet Time:</span>
              <span className="font-bold text-white font-mono">{policy.cooldown_minutes} minutes</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Max 24h Customer Outreach:</span>
              <span className="font-bold text-cyan-400 font-mono">{policy.max_customer_contact_frequency_24h} contacts</span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Permissions Matrix */}
      <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
          <div className="flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-semibold text-white">
              Autonomous Action Permissions
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">4 Recovery Channels</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {permissions.map((perm) => (
            <div
              key={perm.key}
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start justify-between gap-3 text-xs"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-100">{perm.name}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                    ENABLED
                  </span>
                </div>
                <p className="text-slate-400 mt-1.5 leading-relaxed">{perm.desc}</p>
              </div>

              <div className="w-6 h-6 rounded-full bg-emerald-950 flex items-center justify-center text-emerald-400 border border-emerald-800 shrink-0 mt-0.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
