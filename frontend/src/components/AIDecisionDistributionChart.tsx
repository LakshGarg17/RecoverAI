'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Layers } from 'lucide-react';
import { ActionDistribution } from '../lib/types';

interface AIDecisionDistributionChartProps {
  distribution?: ActionDistribution[];
  isLoading?: boolean;
}

export function AIDecisionDistributionChart({
  distribution = [],
  isLoading = false,
}: AIDecisionDistributionChartProps) {
  const colors: Record<string, string> = {
    PAYMENT_LINK: '#8b5cf6', // purple
    PERSONALIZED_REMINDER: '#3b82f6', // blue
    CHECKOUT_REMINDER: '#06b6d4', // cyan
    DELAYED_FOLLOW_UP: '#f59e0b', // amber
    NO_ACTION: '#64748b', // slate
  };

  const actionLabels: Record<string, string> = {
    PAYMENT_LINK: 'Payment Link',
    PERSONALIZED_REMINDER: 'Personalized Msg',
    CHECKOUT_REMINDER: 'Checkout Reminder',
    DELAYED_FOLLOW_UP: 'Delayed Follow-up',
    NO_ACTION: 'No Action',
  };

  const chartData = distribution.map((item) => ({
    ...item,
    displayName: actionLabels[item.action] || item.action,
    fill: colors[item.action] || '#6366f1',
  }));

  return (
    <div className="rounded-xl bg-surface border border-borderDark/80 p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-purple-400" />
            <h3 className="text-base font-semibold text-white">
              AI Action Decision Distribution
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-medium px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/50">
            5 Actions
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Deterministic distribution of recovery interventions chosen across evaluated carts.
        </p>

        <div className="w-full h-56">
          {isLoading ? (
            <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
              Loading distribution...
            </div>
          ) : chartData.length === 0 ? (
            <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
              No decision records found.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis
                  dataKey="displayName"
                  type="category"
                  stroke="#94a3b8"
                  tick={{ fontSize: 11 }}
                  width={110}
                />
                <Tooltip
                  formatter={(value: any, name: string) => [
                    `${value} decisions`,
                    'Count',
                  ]}
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '0.5rem',
                    fontSize: '12px',
                    color: '#fff',
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-borderDark/60 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
        {chartData.map((item) => (
          <div key={item.action} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: item.fill }}
            />
            <span className="text-slate-400 truncate">{item.displayName}:</span>
            <span className="font-semibold text-white">{item.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
