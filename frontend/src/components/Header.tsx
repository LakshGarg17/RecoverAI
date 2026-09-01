'use client';

import React, { useState, useEffect } from 'react';
import {
  Search,
  Activity,
  Play,
  CheckCircle2,
  AlertTriangle,
  Server,
  Database,
  Cpu,
  CreditCard,
  ChevronDown,
} from 'lucide-react';
import { api } from '../lib/api';
import { HealthResponse } from '../lib/types';

interface HeaderProps {
  onOpenDemo?: () => void;
}

export function Header({ onOpenDemo }: HeaderProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [isOpenDetails, setIsOpenDetails] = useState<boolean>(false);
  const [isHealthy, setIsHealthy] = useState<boolean>(true);

  const fetchHealth = () => {
    api.checkHealth()
      .then(({ data, latencyMs, error }) => {
        if (data) {
          setHealth(data);
          setLatency(latencyMs);
          setIsHealthy(data.status === 'ok');
        } else {
          setIsHealthy(false);
        }
      })
      .catch(() => {
        setIsHealthy(false);
      });
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-surface/90 border-b border-borderDark/80 px-6 flex items-center justify-between sticky top-0 z-30 backdrop-blur-md">
      {/* Search Bar */}
      <div className="relative w-72 max-w-xs">
        <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search customer, event, or decision..."
          className="w-full pl-9 pr-4 py-1.5 rounded-xl bg-slate-900/80 border border-borderDark text-xs text-white placeholder-slate-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-all"
        />
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* System Health Dropdown Badge */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsOpenDetails(!isOpenDetails)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-borderDark/80 hover:border-slate-700 text-xs text-slate-300 transition-all"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
              }`}
            />
            <span className="font-medium">
              {isHealthy ? 'Systems Operational' : 'Backend Degraded'}
            </span>
            {latency !== null && (
              <span className="text-[10px] text-slate-500 font-mono">
                {latency}ms
              </span>
            )}
            <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
          </button>

          {/* Details Tooltip / Popover */}
          {isOpenDetails && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl bg-slate-900 border border-borderDark shadow-2xl p-4 text-xs z-50 animate-fadeIn">
              <div className="font-bold text-white mb-2 flex items-center justify-between">
                <span>Infrastructure Telemetry</span>
                <span className="text-[10px] text-slate-500 font-mono">v0.1.0</span>
              </div>
              <div className="space-y-2 text-slate-400">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Server className="w-3.5 h-3.5 text-primary-400" /> FastAPI Backend
                  </span>
                  <span className="text-emerald-400 font-semibold">Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-cyan-400" /> Database Engine
                  </span>
                  <span className="text-emerald-400 font-semibold">Healthy</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-purple-400" /> AI Diagnosis (GPT)
                  </span>
                  <span className="text-emerald-400 font-semibold">Ready</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <CreditCard className="w-3.5 h-3.5 text-amber-400" /> Razorpay Test Mode
                  </span>
                  <span className="text-amber-400 font-semibold">Test Mode</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Run Demo Recovery Trigger */}
        {onOpenDemo && (
          <button
            type="button"
            onClick={onOpenDemo}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-primary-600 hover:bg-primary-500 text-white shadow-neon transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Run Recovery Analysis</span>
          </button>
        )}
      </div>
    </header>
  );
}
