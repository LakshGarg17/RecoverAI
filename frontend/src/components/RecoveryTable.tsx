'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { StatusBadge } from './StatusBadge';
import { RecoveryOpportunity } from '../lib/types';
import { ChevronLeft, ChevronRight, ExternalLink, ArrowRight } from 'lucide-react';

interface RecoveryTableProps {
  opportunities: RecoveryOpportunity[];
  page?: number;
  total?: number;
  totalPages?: number;
  limit?: number;
  onPageChange?: (newPage: number) => void;
  isLoading?: boolean;
}

export function RecoveryTable({
  opportunities = [],
  page = 1,
  total = 0,
  totalPages = 1,
  limit = 15,
  onPageChange,
  isLoading = false,
}: RecoveryTableProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="rounded-xl bg-surface border border-borderDark/80 p-12 text-center text-xs text-slate-400">
        Loading recovery opportunities...
      </div>
    );
  }

  if (!opportunities || opportunities.length === 0) {
    return (
      <div className="rounded-xl bg-surface border border-borderDark/80 p-12 text-center">
        <p className="text-sm font-medium text-slate-300">No recovery opportunities found</p>
        <p className="text-xs text-slate-500 mt-1">Try adjusting your filters or search keywords.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-surface border border-borderDark/80 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-borderDark/80">
            <tr>
              <th scope="col" className="px-5 py-3.5">Event / Customer</th>
              <th scope="col" className="px-5 py-3.5">Cart Value</th>
              <th scope="col" className="px-5 py-3.5">Risk Score</th>
              <th scope="col" className="px-5 py-3.5">Recommended Action</th>
              <th scope="col" className="px-5 py-3.5">Guardrail</th>
              <th scope="col" className="px-5 py-3.5">Status</th>
              <th scope="col" className="px-5 py-3.5 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-borderDark/60">
            {opportunities.map((item) => (
              <tr
                key={item.event_id}
                onClick={() => router.push(`/recovery/${item.event_id}`)}
                className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
              >
                <td className="px-5 py-4">
                  <div className="font-semibold text-white group-hover:text-primary-400 transition-colors">
                    {item.event_id}
                  </div>
                  <div className="text-xs text-slate-500 font-mono mt-0.5">
                    {item.customer_id}
                  </div>
                </td>

                <td className="px-5 py-4">
                  <span className="font-semibold text-white">
                    ₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </td>

                <td className="px-5 py-4">
                  <StatusBadge type="risk" value={item.risk_score} />
                </td>

                <td className="px-5 py-4">
                  <StatusBadge type="action" value={item.ai_action} />
                </td>

                <td className="px-5 py-4">
                  <StatusBadge type="guardrail" value={item.guardrail_status} />
                </td>

                <td className="px-5 py-4">
                  <StatusBadge type="status" value={item.status} />
                </td>

                <td className="px-5 py-4 text-right">
                  <span className="inline-flex items-center text-xs font-medium text-slate-400 group-hover:text-primary-400 transition-colors">
                    View <ArrowRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && onPageChange && (
        <div className="px-5 py-3.5 bg-slate-900/60 border-t border-borderDark/80 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <strong className="text-white">{((page - 1) * limit) + 1}</strong> to{' '}
            <strong className="text-white">{Math.min(page * limit, total)}</strong> of{' '}
            <strong className="text-white">{total.toLocaleString()}</strong> cases
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded-lg border border-borderDark/80 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 text-slate-300 font-medium">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg border border-borderDark/80 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
