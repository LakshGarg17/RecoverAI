'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  DollarSign,
  User,
  ShieldCheck,
  Sparkles,
  ExternalLink,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  CreditCard,
  Layers,
  Send,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../../lib/api';
import { RecoveryDetail, RecoveryRunResult } from '../../../lib/types';
import { StatusBadge } from '../../../components/StatusBadge';
import { AuditTimeline } from '../../../components/AuditTimeline';
import { LoadingState, ErrorState } from '../../../components/StateViews';

export default function RecoveryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = String(params?.id || '');

  const [detail, setDetail] = useState<RecoveryDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [executionMessage, setExecutionMessage] = useState<string | null>(null);

  const loadDetail = async () => {
    if (!eventId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getRecoveryDetail(eventId);
      setDetail(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load recovery case detail.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [eventId]);

  const handleManualExecute = async () => {
    if (!detail) return;
    setIsExecuting(true);
    setExecutionMessage(null);
    try {
      const res = await api.runRecovery({
        event_id: detail.event_id,
        event_data: detail.event_metadata,
      });

      setExecutionMessage(
        res.payment_url
          ? `Razorpay Test Mode link generated: ${res.payment_link_id}`
          : res.reason || 'Execution processed.'
      );
      // Reload detail
      await loadDetail();
    } catch (err: any) {
      setExecutionMessage(`Execution failed: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  if (isLoading) {
    return <LoadingState message={`Analyzing recovery case ${eventId}...`} />;
  }

  if (error || !detail) {
    return <ErrorState message={error || 'Recovery case record not found.'} onRetry={loadDetail} />;
  }

  const isApproved = detail.guardrail_status === 'APPROVED';
  const hasPaymentLink = Boolean(detail.execution.payment_url);

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-xl bg-surface hover:bg-slate-800 border border-borderDark text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight font-mono">
                {detail.event_id}
              </h1>
              <StatusBadge type="guardrail" value={detail.guardrail_status} />
              <StatusBadge type="status" value={detail.execution.status} />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Customer: <span className="font-mono text-slate-300">{detail.customer_id}</span> • Evaluated via RecoverAI Intelligence Layer
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadDetail}
            className="p-2 rounded-xl bg-surface hover:bg-slate-800 border border-borderDark text-slate-400 hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          {isApproved && !hasPaymentLink && (
            <button
              onClick={handleManualExecute}
              disabled={isExecuting}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded-xl shadow-neon transition-all"
            >
              {isExecuting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Dispatching...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  Dispatch Recovery
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {executionMessage && (
        <div className="p-3.5 rounded-xl bg-indigo-950/60 border border-indigo-500/40 text-xs text-indigo-200 flex items-center justify-between">
          <span>{executionMessage}</span>
          <button onClick={() => setExecutionMessage(null)} className="text-indigo-400 hover:text-white font-bold">✕</button>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl bg-surface border border-borderDark/80 p-4">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Cart Value at Risk
          </span>
          <div className="text-xl font-bold text-white mt-1">
            ₹{detail.cart_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Currency: {detail.currency}</span>
        </div>

        <div className="rounded-xl bg-surface border border-borderDark/80 p-4">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Deterministic Risk Score
          </span>
          <div className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            {detail.risk_score.toFixed(1)}/100
            <StatusBadge type="risk" value={detail.risk_score} />
          </div>
          <span className="text-[10px] text-slate-500">Priority: {detail.priority}</span>
        </div>

        <div className="rounded-xl bg-surface border border-borderDark/80 p-4">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Expected Recovery Value
          </span>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            ₹{detail.expected_recovery_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-slate-500">EV Adjusted for friction</span>
        </div>

        <div className="rounded-xl bg-surface border border-borderDark/80 p-4">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Recommended Action
          </span>
          <div className="mt-1">
            <StatusBadge type="action" value={detail.selected_action} />
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">Selected by Decision Engine</span>
        </div>
      </div>

      {/* Main Grid: Left = AI Diagnosis + Guardrails, Right = Execution + Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* AI Diagnosis Card */}
          <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-semibold text-white">
                  AI Diagnosis & Calibrated Dunning
                </h3>
              </div>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-800/60 font-mono">
                {detail.ai_diagnosis_category}
              </span>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Clinical Revenue Loss Diagnosis
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
                {detail.ai_explanation}
              </p>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Personalized Customer Outreach Draft
              </h4>
              <div className="text-xs text-slate-200 bg-indigo-950/20 border border-indigo-800/40 p-3.5 rounded-lg italic leading-relaxed">
                "{detail.suggested_message}"
              </div>
            </div>
          </div>

          {/* 10 Guardrail Safety Checks Table */}
          <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-semibold text-white">
                  Guardrail Safety & Policy Rules (10 Modular Checks)
                </h3>
              </div>
              <span className="text-xs text-slate-400">
                Merchant Policy v1.1
              </span>
            </div>

            <div className="divide-y divide-borderDark/60">
              {detail.checks.map((chk) => {
                const isPassed = chk.status === 'PASSED';
                return (
                  <div key={chk.check_name} className="py-2.5 flex items-start justify-between gap-3 text-xs">
                    <div className="space-y-0.5">
                      <span className="font-mono text-slate-300 font-medium">
                        {chk.check_name.replace(/_/g, ' ')}
                      </span>
                      <p className="text-[11px] text-slate-500">{chk.reason}</p>
                    </div>

                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                        isPassed
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'bg-rose-950 text-rose-300 border border-rose-800'
                      }`}
                    >
                      {isPassed ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {chk.status}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Razorpay Execution + Timeline */}
        <div className="lg:col-span-5 space-y-6">
          {/* Razorpay Test Mode Execution Card */}
          <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
              <div className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-semibold text-white">
                  Execution State
                </h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                Razorpay Test Mode
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Execution Status:</span>
                <StatusBadge type="status" value={detail.execution.status} />
              </div>

              {detail.execution.payment_link_id && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Payment Link ID:</span>
                  <span className="font-mono text-slate-200 font-semibold">{detail.execution.payment_link_id}</span>
                </div>
              )}

              {detail.execution.payment_url && (
                <div className="mt-2 pt-3 border-t border-borderDark">
                  <span className="text-slate-400 block mb-1.5">Customer Payment Checkout Link:</span>
                  <a
                    href={detail.execution.payment_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-neon transition-all"
                  >
                    Open Razorpay Test Checkout <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              )}

              {detail.recovery.status === 'RECOVERED' && (
                <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300">
                  <div className="font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Revenue Successfully Recovered!
                  </div>
                  <div className="text-[11px] text-emerald-200/80 mt-1">
                    Reconciled: ₹{detail.recovery.recovered_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} (Ref: {detail.recovery.payment_id})
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chronological Audit Timeline */}
          <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-semibold text-white">
                  Audit Trail & Decision Sequence
                </h3>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Immutable</span>
            </div>

            <AuditTimeline events={detail.timeline} />
          </div>
        </div>
      </div>
    </div>
  );
}
