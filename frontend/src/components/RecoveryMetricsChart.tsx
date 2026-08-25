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
  BarChart,
  Bar,
} from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';

const recoveryTrendData = [
  { day: 'Day 1', recovered: 4200, outstanding: 18000 },
  { day: 'Day 2', recovered: 8500, outstanding: 15400 },
  { day: 'Day 3', recovered: 14200, outstanding: 11000 },
  { day: 'Day 4', recovered: 19800, outstanding: 8200 },
  { day: 'Day 5', recovered: 26400, outstanding: 5100 },
  { day: 'Day 6', recovered: 31200, outstanding: 3400 },
  { day: 'Day 7', recovered: 35800, outstanding: 1900 },
];

const riskDistributionData = [
  { category: 'Low Risk', invoices: 45, fill: '#10b981' },
  { category: 'Medium Risk', invoices: 28, fill: '#f59e0b' },
  { category: 'High Risk', invoices: 12, fill: '#ef4444' },
  { category: 'Escalated', invoices: 5, fill: '#8b5cf6' },
];

export const RecoveryMetricsChart: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Recovery Curve (Area Chart) */}
      <div className="lg:col-span-2 glass-panel rounded-2xl p-6 border border-borderDark/80">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-primary-400" />
            <h3 className="font-heading text-lg font-bold text-white">
              Autonomous Recovery Simulation
            </h3>
          </div>
          <span className="text-xs text-emerald-400 font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            Recharts Integration Active
          </span>
        </div>
        <p className="text-xs text-gray-400 mb-6">
          Cumulative simulated recovery progress (INR) across dunning cycles.
        </p>

        <div className="w-full h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={recoveryTrendData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="recoveredGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.6} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="outstandingGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
              <XAxis dataKey="day" stroke="#6b7280" tick={{ fontSize: 12 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} tickFormatter={(val) => `₹${val / 1000}k`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111726',
                  borderColor: '#1f293d',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                  color: '#fff',
                }}
              />
              <Area
                type="monotone"
                dataKey="recovered"
                name="Recovered (₹)"
                stroke="#6366f1"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#recoveredGradient)"
              />
              <Area
                type="monotone"
                dataKey="outstanding"
                name="Outstanding (₹)"
                stroke="#f59e0b"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#outstandingGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Category Distribution (Bar Chart) */}
      <div className="glass-panel rounded-2xl p-6 border border-borderDark/80 flex flex-col justify-between">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <h3 className="font-heading text-lg font-bold text-white">Risk Segmentation</h3>
          </div>
          <p className="text-xs text-gray-400 mb-4">
            AI Classification Pipeline Scaffolding.
          </p>

          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistributionData} layout="vertical" margin={{ left: -15, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" horizontal={false} />
                <XAxis type="number" stroke="#6b7280" tick={{ fontSize: 11 }} />
                <YAxis dataKey="category" type="category" stroke="#9ca3af" tick={{ fontSize: 11 }} width={90} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111726',
                    borderColor: '#1f293d',
                    borderRadius: '0.5rem',
                    fontSize: '12px',
                    color: '#fff',
                  }}
                />
                <Bar dataKey="invoices" name="Invoice Count" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="pt-4 border-t border-borderDark/60 flex items-center justify-between text-xs text-gray-400">
          <span>Active Test Invoices: <strong className="text-white">90</strong></span>
          <span className="text-emerald-400 font-semibold">92.4% Projected Recovery</span>
        </div>
      </div>
    </div>
  );
};
