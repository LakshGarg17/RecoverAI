'use client';

import React from 'react';
import { Filter, ArrowRight, CheckCircle2 } from 'lucide-react';
import { FunnelStage } from '../lib/types';

interface RecoveryFunnelProps {
  stages?: FunnelStage[];
  isLoading?: boolean;
}

export function RecoveryFunnel({ stages = [], isLoading = false }: RecoveryFunnelProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl bg-surface border border-borderDark/80 p-6 flex items-center justify-center h-48 text-xs text-slate-400">
        Loading funnel progression...
      </div>
    );
  }

  if (!stages || stages.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl bg-surface border border-borderDark/80 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-white">
            Autonomous Recovery Conversion Funnel
          </h3>
        </div>
        <span className="text-xs text-slate-400">
          5-Stage Risk $\rightarrow$ Recovery Pipeline
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mt-4">
        {stages.map((stage, idx) => {
          const isFinal = idx === stages.length - 1;
          const bgShades = [
            'border-amber-500/30 bg-amber-950/20 text-amber-300',
            'border-blue-500/30 bg-blue-950/20 text-blue-300',
            'border-indigo-500/30 bg-indigo-950/20 text-indigo-300',
            'border-purple-500/30 bg-purple-950/20 text-purple-300',
            'border-emerald-500/40 bg-emerald-950/30 text-emerald-300',
          ];

          return (
            <div
              key={stage.stage}
              className={`relative rounded-xl border p-4 flex flex-col justify-between ${bgShades[idx % bgShades.length]}`}
            >
              <div>
                <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider opacity-80 mb-2">
                  <span>Step 0{idx + 1}</span>
                  {isFinal && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                </div>
                <h4 className="text-sm font-bold text-white leading-snug">{stage.stage}</h4>
                <p className="text-xs opacity-75 mt-1 line-clamp-2">{stage.description}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/10 flex items-baseline justify-between">
                <div>
                  <span className="text-lg font-bold text-white">
                    {stage.count.toLocaleString()}
                  </span>
                  <p className="text-[10px] opacity-70">
                    ₹{stage.value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </p>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white/10 text-white">
                  {stage.conversion_rate}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
