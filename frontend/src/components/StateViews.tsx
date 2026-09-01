'use client';

import React from 'react';
import { Loader2, AlertTriangle, Inbox, RefreshCw } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({ message = 'Loading recovery intelligence...', className = '' }: LoadingStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-12 text-center ${className}`}>
      <Loader2 className="w-8 h-8 text-primary-500 animate-spin mb-4" />
      <p className="text-sm font-medium text-slate-300">{message}</p>
      <p className="text-xs text-slate-500 mt-1">Aggregating telemetry from decision and execution pipelines</p>
    </div>
  );
}

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  title = 'No records found',
  description = 'No recovery opportunities matching the current criteria were identified.',
  actionText,
  onAction,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-12 text-center rounded-xl bg-surface/40 border border-borderDark/60 ${className}`}>
      <div className="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center mb-4 text-slate-500 border border-slate-800">
        <Inbox className="w-6 h-6" />
      </div>
      <h4 className="text-base font-semibold text-slate-200">{title}</h4>
      <p className="text-sm text-slate-400 mt-1 max-w-md">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 text-xs font-medium bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Backend Communication Error',
  message = 'Failed to load live recovery analytics. Ensure the FastAPI backend server is running on http://localhost:8000.',
  onRetry,
  className = '',
}: ErrorStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-10 text-center rounded-xl bg-rose-950/20 border border-rose-900/40 ${className}`}>
      <div className="w-12 h-12 rounded-full bg-rose-950/60 flex items-center justify-center mb-3 text-rose-400 border border-rose-800/60">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h4 className="text-base font-semibold text-rose-200">{title}</h4>
      <p className="text-xs text-rose-300/80 mt-1 max-w-lg leading-relaxed">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 text-xs font-medium bg-rose-900/40 hover:bg-rose-900/70 text-rose-200 rounded-lg border border-rose-700/50 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
}
