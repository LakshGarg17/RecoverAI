'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { HealthStatusCard } from '@/components/HealthStatusCard';
import { RecoveryMetricsChart } from '@/components/RecoveryMetricsChart';
import { api } from '@/lib/api';
import { HealthResponse } from '@/lib/types';
import {
  ShieldCheck,
  Send,
  Zap,
  Sparkles,
  Terminal,
  ArrowUpRight,
  Code2,
  CheckCircle,
} from 'lucide-react';

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  // Quick API tester state
  const [testResult, setTestResult] = useState<any>(null);
  const [testingEndpoint, setTestingEndpoint] = useState<string | null>(null);

  const fetchHealth = async () => {
    setIsLoading(true);
    setError(undefined);
    try {
      const result = await api.checkHealth();
      if (result.error) {
        setError(result.error);
        setHealth(null);
      } else {
        setHealth(result.data);
      }
      setLatencyMs(result.latencyMs);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleTestPaymentOrder = async () => {
    setTestingEndpoint('payments');
    setTestResult(null);
    try {
      const res = await api.createPaymentOrder({
        amount: 49900,
        currency: 'INR',
        receipt: 'rcpt_day1_demo',
        notes: { demo: 'Day 1 Setup Verification' },
      });
      setTestResult({ endpoint: '/api/v1/payments/orders', response: res });
    } catch (err: any) {
      setTestResult({ endpoint: '/api/v1/payments/orders', error: err.message });
    } finally {
      setTestingEndpoint(null);
    }
  };

  const handleTestAIAnalysis = async () => {
    setTestingEndpoint('ai');
    setTestResult(null);
    try {
      const res = await api.analyzeInvoice({
        customer_name: 'Acme SaaS Corp',
        overdue_days: 18,
        amount: 25000,
        currency: 'INR',
        previous_communications: ['email_reminder_1'],
      });
      setTestResult({ endpoint: '/api/v1/ai/analyze', response: res });
    } catch (err: any) {
      setTestResult({ endpoint: '/api/v1/ai/analyze', error: err.message });
    } finally {
      setTestingEndpoint(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Banner */}
        <section className="relative rounded-3xl overflow-hidden glass-panel p-8 sm:p-10 border border-borderDark/80">
          <div className="relative z-10 max-w-3xl space-y-4">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary-500/20 text-primary-300 border border-primary-500/30">
              <Sparkles className="w-3.5 h-3.5 text-primary-400" />
              <span>Project Scaffolding & Architecture Verification</span>
            </div>

            <h1 className="font-heading text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Autonomous AI Payment Recovery Agent
            </h1>

            <p className="text-sm sm:text-base text-gray-300 leading-relaxed">
              RecoverAI unifies automated dunning, LLM-driven empathetic negotiation, and Razorpay
              payment links to autonomously recover delinquent and failed SaaS subscriptions.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <span className="text-xs text-gray-400 font-medium">Stack Target:</span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-surface border border-borderDark text-gray-200">
                Next.js 14
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-surface border border-borderDark text-gray-200">
                FastAPI Python
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-surface border border-borderDark text-gray-200">
                PostgreSQL + SQLAlchemy
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-surface border border-borderDark text-gray-200">
                OpenAI Structured Outputs
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-surface border border-borderDark text-gray-200">
                Razorpay (Test Mode)
              </span>
            </div>
          </div>

          <div className="absolute top-1/2 right-4 -translate-y-1/2 hidden xl:block opacity-30 pointer-events-none">
            <ShieldCheck className="w-80 h-80 text-primary-400" />
          </div>
        </section>

        {/* Backend & Diagnostics Live Health Card */}
        <section>
          <HealthStatusCard
            health={health}
            latencyMs={latencyMs}
            isLoading={isLoading}
            error={error}
            onRefresh={fetchHealth}
          />
        </section>

        {/* Recharts Analytics Preview */}
        <section>
          <RecoveryMetricsChart />
        </section>

        {/* Interactive Endpoint Scaffolding Verification */}
        <section className="glass-panel rounded-2xl p-6 border border-borderDark/80 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-borderDark/60">
            <div>
              <div className="flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-primary-400" />
                <h3 className="font-heading text-lg font-bold text-white">
                  Stub Endpoint Live Verification
                </h3>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Verify backend route handlers and JSON serialization directly from the frontend.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Payment Order Tester */}
            <div className="bg-surface/60 rounded-xl p-5 border border-borderDark flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                    Payments Route
                  </span>
                  <code className="text-[11px] text-gray-400 bg-background px-2 py-0.5 rounded">
                    POST /api/v1/payments/orders
                  </code>
                </div>
                <h4 className="text-sm font-semibold text-white">Create Test Razorpay Order</h4>
                <p className="text-xs text-gray-400 mt-1">
                  Dispatches a simulated payment order payload (Rs. 499.00 INR) to verify Razorpay service.
                </p>
              </div>

              <button
                onClick={handleTestPaymentOrder}
                disabled={testingEndpoint === 'payments'}
                className="mt-4 inline-flex items-center justify-center px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-all disabled:opacity-50"
              >
                <Zap className={`w-3.5 h-3.5 mr-1.5 ${testingEndpoint === 'payments' ? 'animate-bounce' : ''}`} />
                {testingEndpoint === 'payments' ? 'Creating...' : 'Trigger Payments Endpoint'}
              </button>
            </div>

            {/* AI Analyze Tester */}
            <div className="bg-surface/60 rounded-xl p-5 border border-borderDark flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-purple-400">
                    AI Agent Route
                  </span>
                  <code className="text-[11px] text-gray-400 bg-background px-2 py-0.5 rounded">
                    POST /api/v1/ai/analyze
                  </code>
                </div>
                <h4 className="text-sm font-semibold text-white">Evaluate Recovery Strategy</h4>
                <p className="text-xs text-gray-400 mt-1">
                  Sends an overdue invoice profile to test AI agent classification and draft synthesis.
                </p>
              </div>

              <button
                onClick={handleTestAIAnalysis}
                disabled={testingEndpoint === 'ai'}
                className="mt-4 inline-flex items-center justify-center px-4 py-2 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white transition-all disabled:opacity-50"
              >
                <Sparkles className={`w-3.5 h-3.5 mr-1.5 ${testingEndpoint === 'ai' ? 'animate-bounce' : ''}`} />
                {testingEndpoint === 'ai' ? 'Analyzing...' : 'Trigger AI Agent Endpoint'}
              </button>
            </div>
          </div>

          {/* Test Response Display Box */}
          {testResult && (
            <div className="mt-4 p-4 rounded-xl bg-background/80 border border-borderDark text-xs font-mono">
              <div className="flex items-center justify-between mb-2 pb-2 border-b border-borderDark/60">
                <span className="text-gray-400">
                  Response from: <strong className="text-white">{testResult.endpoint}</strong>
                </span>
                <span className={testResult.error ? 'text-red-400' : 'text-emerald-400 font-semibold'}>
                  {testResult.error ? 'Error' : '200 OK'}
                </span>
              </div>
              <pre className="text-gray-300 overflow-x-auto p-2 bg-surface rounded-lg">
                {JSON.stringify(testResult.response || testResult.error, null, 2)}
              </pre>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-borderDark/80 bg-surface/30 mt-12 py-6 text-center text-xs text-gray-500">
        <p>RecoverAI © 2026. Built with Next.js, FastAPI, SQLAlchemy, OpenAI, & Razorpay.</p>
      </footer>
    </div>
  );
}
