'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  Play,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ExternalLink,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { DemoRecoveryCase, RecoveryRunResult } from '../lib/types';
import { StatusBadge } from './StatusBadge';

interface DemoRecoveryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function DemoRecoveryModal({
  isOpen,
  onClose,
  onSuccess,
}: DemoRecoveryModalProps) {
  const [demoCases, setDemoCases] = useState<DemoRecoveryCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [result, setResult] = useState<RecoveryRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingCases, setIsLoadingCases] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;

    setDemoCases([]);
    setSelectedCaseId('');
    setResult(null);
    setError(null);
    setCurrentStep(0);
    setIsLoadingCases(true);

    api
      .getDemoCases()
      .then((cases) => {
        if (!Array.isArray(cases)) {
          throw new Error(
            'Invalid demo case response received from backend.'
          );
        }

        setDemoCases(cases);

        if (cases.length > 0) {
          setSelectedCaseId(cases[0].case_id);
        } else {
          setError(
            'No demo recovery cases are available. Please check the backend demo data.'
          );
        }
      })
      .catch((err: unknown) => {
        console.error(
          'Failed to load demo recovery cases:',
          err
        );

        setDemoCases([]);
        setSelectedCaseId('');

        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load demo recovery cases.'
        );
      })
      .finally(() => {
        setIsLoadingCases(false);
      });
  }, [isOpen]);

  if (!isOpen) return null;

  const selectedCase = demoCases.find(
    (c) => c.case_id === selectedCaseId
  );

  const handleExecute = async () => {
    if (!selectedCase) {
      setError('Please select a recovery test case first.');
      return;
    }

    setIsRunning(true);
    setError(null);
    setResult(null);
    setCurrentStep(1);

    try {
      /*
       * Visual pipeline animation.
       * The actual recovery pipeline is executed by the backend.
       */
      const aiTimer = window.setTimeout(() => {
        setCurrentStep(2);
      }, 600);

      const decisionTimer = window.setTimeout(() => {
        setCurrentStep(3);
      }, 1200);

      const payload = {
        event_id: selectedCase.event_data.event_id,
        event_data: selectedCase.event_data,
        current_purchase_status:
          selectedCase.event_data.purchase_status,
      };

      const res = await api.runRecovery(payload);

      /*
       * Stop the intermediate animation timers because
       * the API request has completed.
       */
      window.clearTimeout(aiTimer);
      window.clearTimeout(decisionTimer);

      window.setTimeout(() => {
        setCurrentStep(4);
        setResult(res);
        setIsRunning(false);

        if (onSuccess) {
          onSuccess();
        }
      }, 1600);
    } catch (err: unknown) {
      console.error(
        'Recovery pipeline failed:',
        err
      );

      setIsRunning(false);
      setCurrentStep(0);

      setError(
        err instanceof Error
          ? err.message
          : 'Pipeline execution failed. Please check the backend logs.'
      );
    }
  };

  const steps = [
    {
      title: 'Deterministic Risk Scoring',
      desc: 'Intent heuristics, cart value, and session analysis',
    },
    {
      title: 'AI Diagnosis & Dunning Calibration',
      desc: 'GPT-4o-mini structured diagnosis & tone generation',
    },
    {
      title: 'Decision & Guardrail Engine',
      desc: '10 Safety rules, cooldown, and transaction limits',
    },
    {
      title: 'Razorpay Execution / Dispatch',
      desc: 'Test Mode payment link or bounded rejection',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl rounded-2xl bg-surface border border-borderDark/90 shadow-2xl p-6 overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-borderDark/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Sparkles className="w-4 h-4" />
            </div>

            <div>
              <h3 className="text-base font-bold text-white">
                Live Recovery Pipeline Demo Runner
              </h3>

              <p className="text-xs text-slate-400">
                Execute end-to-end recovery through Risk Engine
                → AI → Guardrails → Razorpay
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Close recovery demo"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Case Selector */}
        <div className="mt-5">
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Select E-Commerce Test Case
          </label>

          {/* Loading */}
          {isLoadingCases && (
            <div className="flex items-center justify-center gap-2 p-6 rounded-xl bg-slate-900/60 border border-borderDark/60 text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" />

              <span className="text-xs">
                Loading recovery test cases...
              </span>
            </div>
          )}

          {/* No cases */}
          {!isLoadingCases && demoCases.length === 0 && (
            <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/60">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />

                <div>
                  <div className="text-xs font-semibold text-rose-300">
                    No demo cases available
                  </div>

                  <div className="text-[11px] text-slate-400 mt-1">
                    {error ||
                      'The backend did not return any recovery test cases.'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Cases */}
          {!isLoadingCases && demoCases.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {demoCases.map((c) => {
                const cartValue = Number(
                  c?.event_data?.cart_value ?? 0
                );

                return (
                  <button
                    key={c.case_id}
                    type="button"
                    onClick={() => {
                      setSelectedCaseId(c.case_id);
                      setResult(null);
                      setError(null);
                      setCurrentStep(0);
                    }}
                    className={`text-left p-3 rounded-xl border transition-all ${selectedCaseId === c.case_id
                        ? 'bg-indigo-950/40 border-indigo-500 text-white shadow-neon'
                        : 'bg-slate-900/60 border-borderDark/60 text-slate-400 hover:border-slate-700'
                      }`}
                  >
                    <div className="text-xs font-bold text-white">
                      {String(c.case_id || 'UNKNOWN')
                        .replace(/_/g, ' ')
                        .toUpperCase()}
                    </div>

                    <div className="text-[11px] text-slate-400 mt-1 line-clamp-1">
                      {c.description || 'Recovery test scenario'}
                    </div>

                    <div className="mt-2 text-xs font-semibold text-emerald-400">
                      ₹{cartValue.toLocaleString('en-IN')}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Pipeline Execution Animation */}
        {isRunning && (
          <div className="mt-6 p-4 rounded-xl bg-slate-900/90 border border-indigo-500/30">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Autonomous Pipeline Execution in Progress
            </h4>

            <div className="space-y-3">
              {steps.map((st, i) => {
                const stepNum = i + 1;
                const isCurrent = currentStep === stepNum;
                const isPassed = currentStep > stepNum;

                return (
                  <div
                    key={st.title}
                    className="flex items-center gap-3"
                  >
                    <div className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold">
                      {isPassed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-slate-700" />
                      )}
                    </div>

                    <div>
                      <div
                        className={`text-xs font-medium ${isCurrent
                            ? 'text-indigo-300 font-bold'
                            : isPassed
                              ? 'text-white'
                              : 'text-slate-500'
                          }`}
                      >
                        {st.title}
                      </div>

                      <div className="text-[10px] text-slate-500">
                        {st.desc}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Results Box */}
        {result && (
          <div className="mt-6 p-4 rounded-xl bg-slate-900 border border-borderDark space-y-3">

            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase">
                Live Pipeline Outcome
              </span>

              <StatusBadge
                type="guardrail"
                value={result.guardrail_status}
              />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-xs">

              {/* Risk Score */}
              <div>
                <span className="text-slate-500 text-[10px]">
                  Risk Score
                </span>

                <div className="font-bold text-white">
                  {Number(
                    result.risk_score ?? 0
                  ).toFixed(1)}
                  /100
                </div>
              </div>

              {/* Selected Action */}
              <div>
                <span className="text-slate-500 text-[10px]">
                  Selected Action
                </span>

                <div className="font-bold text-indigo-300">
                  {result.selected_action || 'NO_ACTION'}
                </div>
              </div>

              {/* Expected Value */}
              <div>
                <span className="text-slate-500 text-[10px]">
                  Expected Value
                </span>

                <div className="font-bold text-emerald-400">
                  ₹
                  {Number(
                    result.expected_recovery_value ?? 0
                  ).toFixed(2)}
                </div>
              </div>

              {/* Execution */}
              <div>
                <span className="text-slate-500 text-[10px]">
                  Execution
                </span>

                <div className="font-bold text-white">
                  {result.execution_status || 'UNKNOWN'}
                </div>
              </div>
            </div>

            {/* Razorpay Payment Link */}
            {result.payment_url && (
              <div className="mt-3 p-3 rounded-lg bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-white">
                    Razorpay Test Mode Checkout Ready
                  </div>

                  <div className="text-[10px] text-slate-400 font-mono">
                    {result.payment_link_id ||
                      'Payment link created'}
                  </div>
                </div>

                <a
                  href={result.payment_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
                >
                  Pay Test Link
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            )}

            {/* Guardrail Block */}
            {String(
              result.guardrail_status || ''
            ).toUpperCase() !== 'APPROVED' && (
                <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-900/60 text-xs text-rose-300 flex items-start gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />

                  <div>
                    <strong>
                      Bounded Autonomy Safeguard:
                    </strong>{' '}
                    {result.reason ||
                      'Guardrails prevented execution.'}
                  </div>
                </div>
              )}
          </div>
        )}

        {/* Error */}
        {error && demoCases.length > 0 && (
          <div className="mt-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />

            <div>{error}</div>
          </div>
        )}

        {/* Modal Actions */}
        <div className="mt-6 pt-4 border-t border-borderDark flex items-center justify-end gap-3">

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white transition-colors"
          >
            Close
          </button>

          <button
            type="button"
            disabled={
              isRunning ||
              isLoadingCases ||
              !selectedCase
            }
            onClick={handleExecute}
            className="inline-flex items-center gap-2 px-5 py-2 text-xs font-bold bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl shadow-neon transition-all"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Executing Pipeline...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                Run Pipeline Analysis
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}