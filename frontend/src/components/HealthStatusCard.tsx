'use client';

import React from 'react';
import { HealthResponse } from '@/lib/types';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Database,
  Cpu,
  CreditCard,
  Server,
  Zap,
} from 'lucide-react';

interface HealthStatusCardProps {
  health: HealthResponse | null;
  latencyMs: number | null;
  isLoading: boolean;
  error?: string;
  onRefresh: () => void;
}

export const HealthStatusCard: React.FC<HealthStatusCardProps> = ({
  health,
  latencyMs,
  isLoading,
  error,
  onRefresh,
}) => {
  const isConnected = !!health && !error;

  const getStatusBadge = (status?: string) => {
    if (!status) return null;
    if (status === 'healthy' || status === 'ok' || status === 'configured') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          {status}
        </span>
      );
    }
    if (status === 'placeholder_mode') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/15 text-amber-300 border border-amber-500/30">
          <Zap className="w-3 h-3 mr-1" />
          Test / Mock Ready
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/15 text-red-400 border border-red-500/30">
        <AlertTriangle className="w-3 h-3 mr-1" />
        {status}
      </span>
    );
  };

  return (
    <div className="glass-panel rounded-2xl p-6 relative overflow-hidden border border-borderDark/80 shadow-2xl">
      {/* Background glow accent */}
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-borderDark/60">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="font-heading text-xl font-bold text-white flex items-center">
              Backend Connectivity Hub
            </h2>
            {isConnected ? (
              <span className="flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
                Connected
              </span>
            ) : (
              <span className="flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/40">
                <span className="w-2 h-2 rounded-full bg-red-400 mr-1.5"></span>
                Disconnected
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Real-time diagnostics from <code className="text-primary-300 bg-surface px-1 py-0.5 rounded">/api/health</code>
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center justify-center px-4 py-2 rounded-xl text-xs font-semibold bg-primary-600 hover:bg-primary-500 text-white transition-all shadow-neon disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? 'Pinging Backend...' : 'Ping Diagnostics'}
        </button>
      </div>

      {/* Latency & Main info */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 my-6">
        <div className="bg-surface/70 rounded-xl p-3 border border-borderDark/60">
          <p className="text-[11px] font-medium text-gray-400">Response Latency</p>
          <p className="text-xl font-heading font-bold text-white mt-1">
            {latencyMs !== null ? `${latencyMs} ms` : '--'}
          </p>
        </div>
        <div className="bg-surface/70 rounded-xl p-3 border border-borderDark/60">
          <p className="text-[11px] font-medium text-gray-400">Environment</p>
          <p className="text-xl font-heading font-bold text-primary-300 capitalize mt-1">
            {health?.environment || 'development'}
          </p>
        </div>
        <div className="bg-surface/70 rounded-xl p-3 border border-borderDark/60">
          <p className="text-[11px] font-medium text-gray-400">API Version</p>
          <p className="text-xl font-heading font-bold text-white mt-1">
            v{health?.version || '0.1.0'}
          </p>
        </div>
        <div className="bg-surface/70 rounded-xl p-3 border border-borderDark/60">
          <p className="text-[11px] font-medium text-gray-400">Gateway</p>
          <p className="text-xl font-heading font-bold text-cyan-400 mt-1">FastAPI</p>
        </div>
      </div>

      {/* Error Banner if disconnected */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 flex items-start space-x-3">
          <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Backend Unreachable</p>
            <p className="mt-0.5 text-gray-300">
              Ensure FastAPI backend is running via <code className="bg-black/30 px-1 py-0.5 rounded text-red-200">python run.py</code> on port 8000.
            </p>
            <p className="mt-1 text-[11px] text-gray-400">{error}</p>
          </div>
        </div>
      )}

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* FastAPI Backend */}
        <div className="glass-panel-hover rounded-xl p-4 bg-surface/50 border border-borderDark/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-primary-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">FastAPI Core</p>
              <p className="text-xs text-gray-400">CORS & Routing Layer</p>
            </div>
          </div>
          <div>{getStatusBadge(health?.services?.backend?.status || (isConnected ? 'healthy' : 'disconnected'))}</div>
        </div>

        {/* Database */}
        <div className="glass-panel-hover rounded-xl p-4 bg-surface/50 border border-borderDark/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">SQLAlchemy & DB</p>
              <p className="text-xs text-gray-400">
                {health?.services?.database?.details?.engine
                  ? `Engine: ${health.services.database.details.engine}`
                  : 'Postgres / SQLite'}
              </p>
            </div>
          </div>
          <div>{getStatusBadge(health?.services?.database?.status || (isConnected ? 'healthy' : 'disconnected'))}</div>
        </div>

        {/* Razorpay */}
        <div className="glass-panel-hover rounded-xl p-4 bg-surface/50 border border-borderDark/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Razorpay Payments</p>
              <p className="text-xs text-gray-400">Test Mode Gateway</p>
            </div>
          </div>
          <div>{getStatusBadge(health?.services?.razorpay?.status || (isConnected ? 'placeholder_mode' : 'disconnected'))}</div>
        </div>

        {/* OpenAI */}
        <div className="glass-panel-hover rounded-xl p-4 bg-surface/50 border border-borderDark/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">OpenAI Structured AI</p>
              <p className="text-xs text-gray-400">Decision Engine</p>
            </div>
          </div>
          <div>{getStatusBadge(health?.services?.openai?.status || (isConnected ? 'placeholder_mode' : 'disconnected'))}</div>
        </div>
      </div>
    </div>
  );
};
