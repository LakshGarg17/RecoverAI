'use client';

import React, { useState, useEffect } from 'react';
import { RefreshCw, Search, Receipt, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '../../lib/api';
import { TransactionItem } from '../../lib/types';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingState, ErrorState } from '../../components/StateViews';

export default function TransactionsPage() {
  const [items, setItems] = useState<TransactionItem[]>([]);
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadTransactions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getTransactions({
        page,
        limit: 15,
        status: statusFilter,
        search: search.trim() || undefined,
      });

      setItems(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setError(err.message || 'Failed to load transaction ledger.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadTransactions();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-heading flex items-center gap-2">
            Payment & Recovery Transactions
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {total.toLocaleString()} Records
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Reconciled payments and recovery executions initiated through Razorpay Test Mode.
          </p>
        </div>

        <button
          onClick={() => {
            setPage(1);
            loadTransactions();
          }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-surface hover:bg-slate-800 border border-borderDark rounded-xl transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Ledger
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-xl bg-surface border border-borderDark/80 flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by transaction, customer, or payment ID..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-borderDark text-xs text-white placeholder-slate-500 focus:outline-none focus:border-primary-500"
          />
        </form>

        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-xs text-slate-300 focus:outline-none focus:border-primary-500"
          >
            <option value="ALL">All Payment Statuses</option>
            <option value="RECOVERED">Recovered (Success)</option>
            <option value="PENDING">Pending Checkout</option>
            <option value="FAILED">Failed / Rejected</option>
          </select>
        </div>
      </div>

      {/* Transactions Table */}
      {isLoading ? (
        <LoadingState message="Querying transaction records..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadTransactions} />
      ) : (
        <div className="rounded-xl bg-surface border border-borderDark/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-borderDark/80">
                <tr>
                  <th scope="col" className="px-5 py-3.5">Transaction ID</th>
                  <th scope="col" className="px-5 py-3.5">Customer</th>
                  <th scope="col" className="px-5 py-3.5">Amount</th>
                  <th scope="col" className="px-5 py-3.5">Action</th>
                  <th scope="col" className="px-5 py-3.5">Gateway Payment ID</th>
                  <th scope="col" className="px-5 py-3.5">Status</th>
                  <th scope="col" className="px-5 py-3.5">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderDark/60 text-xs">
                {items.map((it) => (
                  <tr key={it.transaction_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5 font-mono text-white font-medium">
                      {it.transaction_id}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-slate-400">
                      {it.customer_id}
                    </td>
                    <td className="px-5 py-3.5 font-semibold text-white">
                      ₹{it.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge type="action" value={it.action} />
                    </td>
                    <td className="px-5 py-3.5 font-mono text-slate-400">
                      {it.payment_id || '—'}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge type="status" value={it.status} />
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 font-mono text-[11px]">
                      {it.created_at.slice(0, 19).replace('T', ' ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="px-5 py-3.5 bg-slate-900/60 border-t border-borderDark/80 flex items-center justify-between text-xs text-slate-400">
              <div>
                Showing <strong className="text-white">{((page - 1) * 15) + 1}</strong> to{' '}
                <strong className="text-white">{Math.min(page * 15, total)}</strong> of{' '}
                <strong className="text-white">{total.toLocaleString()}</strong> transactions
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page <= 1}
                  className="p-1.5 rounded-lg border border-borderDark/80 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-2 text-slate-300 font-medium">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages}
                  className="p-1.5 rounded-lg border border-borderDark/80 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
