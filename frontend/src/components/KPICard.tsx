'use client';

import React from 'react';
import { LucideIcon, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: string;
  isPositive?: boolean;
  icon: LucideIcon;
  accentColor?: 'indigo' | 'emerald' | 'amber' | 'cyan' | 'purple';
}

export function KPICard({
  title,
  value,
  subtitle,
  change,
  isPositive = true,
  icon: Icon,
  accentColor = 'indigo',
}: KPICardProps) {
  const colorMap = {
    indigo: 'from-indigo-500/20 to-transparent text-indigo-400 border-indigo-500/20',
    emerald: 'from-emerald-500/20 to-transparent text-emerald-400 border-emerald-500/20',
    amber: 'from-amber-500/20 to-transparent text-amber-400 border-amber-500/20',
    cyan: 'from-cyan-500/20 to-transparent text-cyan-400 border-cyan-500/20',
    purple: 'from-purple-500/20 to-transparent text-purple-400 border-purple-500/20',
  };

  const iconBgMap = {
    indigo: 'bg-indigo-950/60 text-indigo-400 border-indigo-800/60',
    emerald: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60',
    amber: 'bg-amber-950/60 text-amber-400 border-amber-800/60',
    cyan: 'bg-cyan-950/60 text-cyan-400 border-cyan-800/60',
    purple: 'bg-purple-950/60 text-purple-400 border-purple-800/60',
  };

  return (
    <div className="relative overflow-hidden rounded-xl bg-surface border border-borderDark/80 p-5 transition-all duration-200 hover:border-slate-700">
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl ${colorMap[accentColor]} rounded-full blur-2xl pointer-events-none -mr-10 -mt-10`} />

      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </span>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${iconBgMap[accentColor]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <h3 className="text-2xl font-bold tracking-tight text-white">{value}</h3>
        {change && (
          <span
            className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${
              isPositive
                ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/50'
                : 'bg-rose-950/80 text-rose-400 border border-rose-800/50'
            }`}
          >
            {isPositive ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />}
            {change}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-2 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}
