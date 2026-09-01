'use client';

import React from 'react';
import { Settings, CreditCard, Sparkles, Database, ShieldAlert, Key, Bell } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight font-heading flex items-center gap-2">
          Merchant Settings & Integrations
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Gateway environment, AI prompt calibration parameters, and infrastructure connectivity.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Payment Gateway Configuration */}
        <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
            <div className="flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-semibold text-white">
                Razorpay Payment Gateway
              </h3>
            </div>
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-400 border border-amber-800">
              Test Mode
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Razorpay Key ID</label>
              <input
                type="text"
                disabled
                value="rzp_test_••••••••••••"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-slate-400 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Webhook Endpoint URL</label>
              <input
                type="text"
                disabled
                value="http://localhost:8000/api/webhooks/razorpay"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-slate-400 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Webhook Secret Verification</label>
              <div className="flex items-center gap-2 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                HMAC-SHA256 Cryptographic Signature Active
              </div>
            </div>
          </div>
        </div>

        {/* AI Model & Diagnosis Engine */}
        <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-400" />
              <h3 className="text-base font-semibold text-white">
                AI Diagnosis Agent
              </h3>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-800">
              GPT-4o-mini
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Diagnosis Engine Model</label>
              <input
                type="text"
                disabled
                value="openai/gpt-4o-mini (Structured Output)"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-slate-400 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Deterministic Fallback Mechanism</label>
              <input
                type="text"
                disabled
                value="Enabled (Heuristic Intent Calibration on Timeout/Error)"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-slate-400 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Tone & Persona</label>
              <input
                type="text"
                disabled
                value="Empathetic, brand-conscious e-commerce assistance"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-slate-400"
              />
            </div>
          </div>
        </div>

        {/* Database & Persistence */}
        <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-cyan-400" />
              <h3 className="text-base font-semibold text-white">
                Database & Schema Engine
              </h3>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
              SQLAlchemy 2.0
            </span>
          </div>

          <div className="space-y-2.5 text-xs text-slate-400">
            <div className="flex items-center justify-between">
              <span>Engine Dialect:</span>
              <span className="font-mono text-white">SQLite / PostgreSQL (Neon/Supabase ready)</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Schema Version:</span>
              <span className="font-mono text-white">Alembic 0002_recovery_execution</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Audit Log Immutability:</span>
              <span className="text-emerald-400 font-semibold">Strict Append-Only</span>
            </div>
          </div>
        </div>

        {/* Guardrail Policy Overview */}
        <div className="rounded-xl bg-surface border border-borderDark/80 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderDark/80 pb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-semibold text-white">
                Bounded Autonomy Governance
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Active Mode
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            All AI recommendations must satisfy the 10 deterministic guardrail rules before Razorpay checkout links are generated. If any check fails, the recovery action is blocked with zero customer outreach or external gateway charges.
          </p>
        </div>
      </div>
    </div>
  );
}
