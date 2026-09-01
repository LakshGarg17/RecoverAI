'use client';

import React, { useState, useEffect } from 'react';
import { RefreshCw, Filter, Search, ShieldCheck } from 'lucide-react';
import { api } from '../../lib/api';
import { RecoveryOpportunity } from '../../lib/types';
import { RecoveryTable } from '../../components/RecoveryTable';
import { LoadingState, ErrorState } from '../../components/StateViews';

export default function RecoveryOpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<RecoveryOpportunity[]>([]);
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [actionFilter, setActionFilter] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadOpportunities = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getOpportunities({
        page,
        limit: 15,
        status: statusFilter,
        risk: riskFilter,
        action: actionFilter,
        search: search.trim() || undefined,
      });

      setOpportunities(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setError(err.message || 'Failed to load recovery opportunities.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [page, statusFilter, riskFilter, actionFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadOpportunities();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-heading flex items-center gap-2">
            Recovery Opportunities
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800">
              {total.toLocaleString()} Cases
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Browse and inspect all high-risk revenue dropoffs with AI diagnoses and guardrail outcomes.
          </p>
        </div>

        <button
          onClick={() => {
            setPage(1);
            loadOpportunities();
          }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-surface hover:bg-slate-800 border border-borderDark rounded-xl transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh List
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-xl bg-surface border border-borderDark/80 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by event or customer ID..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-borderDark text-xs text-white placeholder-slate-500 focus:outline-none focus:border-primary-500"
          />
        </form>

        {/* Dropdown Filters */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-xs text-slate-300 focus:outline-none focus:border-primary-500"
          >
            <option value="ALL">All Guardrail Statuses</option>
            <option value="APPROVED">Approved Only</option>
            <option value="BLOCKED">Blocked by Guardrail</option>
            <option value="RECOVERED">Recovered</option>
            <option value="ACTIVE">Active Pipeline</option>
          </select>

          {/* Risk Level Filter */}
          <select
            value={riskFilter}
            onChange={(e) => {
              setRiskFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-xs text-slate-300 focus:outline-none focus:border-primary-500"
          >
            <option value="ALL">All Risk Scores</option>
            <option value="CRITICAL">Critical (85+)</option>
            <option value="HIGH">High (70-84)</option>
            <option value="MEDIUM">Medium (50-69)</option>
            <option value="LOW">Low (&lt;50)</option>
          </select>

          {/* Action Filter */}
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-lg bg-slate-900 border border-borderDark text-xs text-slate-300 focus:outline-none focus:border-primary-500"
          >
            <option value="ALL">All Recovery Actions</option>
            <option value="PAYMENT_LINK">Payment Link</option>
            <option value="PERSONALIZED_REMINDER">Personalized Reminder</option>
            <option value="CHECKOUT_REMINDER">Checkout Reminder</option>
            <option value="DELAYED_FOLLOW_UP">Delayed Follow-up</option>
            <option value="NO_ACTION">No Action</option>
          </select>
        </div>
      </div>

      {/* Main Table View */}
      {isLoading ? (
        <LoadingState message="Filtering recovery cases..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadOpportunities} />
      ) : (
        <RecoveryTable
          opportunities={opportunities}
          page={page}
          total={total}
          totalPages={totalPages}
          limit={15}
          onPageChange={(p) => setPage(p)}
        />
      )}
    </div>
  );
}
