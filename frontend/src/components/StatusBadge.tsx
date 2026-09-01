'use client';

import React from 'react';

interface StatusBadgeProps {
  type: 'risk' | 'guardrail' | 'status' | 'action' | 'priority';
  value: string | number;
  className?: string;
}

export function StatusBadge({ type, value, className = '' }: StatusBadgeProps) {
  const strVal = String(value).toUpperCase();

  if (type === 'risk') {
    const num = typeof value === 'number' ? value : parseFloat(value) || 0;
    if (num >= 85) {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-950/80 text-red-400 border border-red-800/60 ${className}`}>
          Critical ({num.toFixed(1)})
        </span>
      );
    }
    if (num >= 70) {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800/60 ${className}`}>
          High ({num.toFixed(1)})
        </span>
      );
    }
    if (num >= 50) {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-950/80 text-blue-400 border border-blue-800/60 ${className}`}>
          Medium ({num.toFixed(1)})
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-700 ${className}`}>
        Low ({num.toFixed(1)})
      </span>
    );
  }

  if (type === 'guardrail') {
    if (strVal === 'APPROVED') {
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 ${className}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Approved
        </span>
      );
    }
    if (strVal === 'BLOCKED' || strVal === 'REJECTED') {
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/80 text-rose-300 border border-rose-800/60 ${className}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
          Blocked
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-800/60 ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
        Review Required
      </span>
    );
  }

  if (type === 'status') {
    if (strVal === 'RECOVERED' || strVal === 'SUCCEEDED' || strVal === 'COMPLETED') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800 ${className}`}>
          Recovered
        </span>
      );
    }
    if (strVal === 'ACTIVE' || strVal === 'CREATED' || strVal === 'PENDING' || strVal === 'EXECUTING') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-950 text-indigo-300 border border-indigo-800 ${className}`}>
          Active
        </span>
      );
    }
    if (strVal === 'FAILED' || strVal === 'EXPIRED') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-900 text-slate-400 border border-slate-700 ${className}`}>
          {strVal}
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-900 text-slate-400 border border-slate-700 ${className}`}>
        {strVal}
      </span>
    );
  }

  if (type === 'action') {
    if (strVal === 'PAYMENT_LINK') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-950/80 text-purple-300 border border-purple-800/60 ${className}`}>
          Payment Link (Razorpay)
        </span>
      );
    }
    if (strVal === 'PERSONALIZED_REMINDER') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-950/80 text-blue-300 border border-blue-800/60 ${className}`}>
          Personalized Reminder
        </span>
      );
    }
    if (strVal === 'CHECKOUT_REMINDER') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 ${className}`}>
          Checkout Reminder
        </span>
      );
    }
    if (strVal === 'DELAYED_FOLLOW_UP') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-800/60 ${className}`}>
          Delayed Follow-up
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-900 text-slate-400 border border-slate-700 ${className}`}>
        No Action
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 ${className}`}>
      {strVal}
    </span>
  );
}
