'use client';

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { TrendingUp, ShieldCheck } from 'lucide-react';
import { RecoveryTrendPoint } from '../lib/types';

interface RecoveryMetricsChartProps {
  data?: RecoveryTrendPoint[];
  isLoading?: boolean;
}

export function RecoveryMetricsChart({ data = [], isLoading = false }: RecoveryMetricsChartProps) {
  const formattedData = data.map((item) => ({
    ...item,
    formattedDate: item.date.length > 5 ? item.date.slice(5) : item.date,
  }));

  const totalAtRisk = data.reduce((acc, curr) => acc + curr.at_risk, 0);
  const totalRecovered = data.reduce((acc, curr) => acc + curr.recovered, 0);
  const avgRecoveryRate = totalAtRisk > 0 ? ((totalRecovered / totalAtRisk) * 100).toFixed(1) : '18.5';

  return (
    <div className="rounded-xl bg-surface border border-borderDark/80 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-400" />
            <h3 className="text-base font-semibold text-white">
              Revenue Recovery Velocity Curve
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Daily comparison of revenue identified at risk vs. successfully recovered (INR).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800/60">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            {avgRecoveryRate}% Avg Efficiency
          </span>
        </div>
      </div>

      <div className="w-full h-72">
        {isLoading ? (
          <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
            Loading recovery trend points...
          </div>
        ) : formattedData.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
            No recovery trend data available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="atRiskGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="recoveredGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="formattedDate" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
              />
              <Tooltip
                formatter={(value: any, name: string) => [
                  `₹${Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
                  name === 'at_risk' ? 'Revenue at Risk' : 'Recovered Revenue',
                ]}
                labelFormatter={(label) => `Date: ${label}`}
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#1e293b',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                  color: '#fff',
                  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
                }}
              />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ paddingBottom: '12px', fontSize: '12px' }}
                formatter={(value) => (value === 'at_risk' ? 'Revenue at Risk' : 'Recovered Revenue')}
              />
              <Area
                type="monotone"
                dataKey="at_risk"
                name="at_risk"
                stroke="#f59e0b"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#atRiskGradient)"
              />
              <Area
                type="monotone"
                dataKey="recovered"
                name="recovered"
                stroke="#10b981"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#recoveredGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
