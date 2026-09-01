'use client';

import React from 'react';
import {
  CheckCircle2,
  AlertOctagon,
  Clock,
  Send,
  CreditCard,
  Sparkles,
  ShieldCheck,
  Ban,
} from 'lucide-react';
import { AuditTimelineEvent } from '../lib/types';

interface AuditTimelineProps {
  events: AuditTimelineEvent[];
}

export function AuditTimeline({ events = [] }: AuditTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-slate-400">
        No audit events recorded for this session.
      </div>
    );
  }

  const getStageIcon = (stage: string, status: string) => {
    if (status === 'BLOCKED' || stage === 'GUARDRAILS_BLOCKED') {
      return <Ban className="w-4 h-4 text-rose-400" />;
    }
    if (stage === 'RECOVERY_IDENTIFIED') {
      return <Clock className="w-4 h-4 text-amber-400" />;
    }
    if (stage === 'RISK_SCORED') {
      return <ShieldCheck className="w-4 h-4 text-blue-400" />;
    }
    if (stage === 'AI_DIAGNOSED') {
      return <Sparkles className="w-4 h-4 text-purple-400" />;
    }
    if (stage === 'ACTION_RECOMMENDED') {
      return <Send className="w-4 h-4 text-indigo-400" />;
    }
    if (stage === 'GUARDRAILS_EVALUATED') {
      return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    }
    if (stage === 'PAYMENT_LINK_CREATED' || stage === 'REVENUE_RECOVERED') {
      return <CreditCard className="w-4 h-4 text-emerald-400" />;
    }
    return <CheckCircle2 className="w-4 h-4 text-slate-400" />;
  };

  const getBadgeStyle = (status: string) => {
    if (status === 'BLOCKED') {
      return 'bg-rose-950/80 text-rose-300 border-rose-800/80';
    }
    if (status === 'COMPLETED') {
      return 'bg-slate-900 text-slate-300 border-slate-700';
    }
    return 'bg-slate-900 text-slate-400 border-slate-800';
  };

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
      {events.map((evt, idx) => {
        const isBlocked = evt.status === 'BLOCKED' || evt.stage === 'GUARDRAILS_BLOCKED';

        return (
          <div key={`${evt.stage}-${idx}`} className="relative group">
            {/* Timeline Icon Marker */}
            <div
              className={`absolute -left-6 top-1.5 w-6 h-6 rounded-full flex items-center justify-center border ${
                isBlocked
                  ? 'bg-rose-950 border-rose-700 text-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.3)]'
                  : 'bg-slate-900 border-slate-700 text-slate-300'
              }`}
            >
              {getStageIcon(evt.stage, evt.status)}
            </div>

            {/* Event Body Card */}
            <div
              className={`rounded-xl border p-4 transition-all ${
                isBlocked
                  ? 'bg-rose-950/20 border-rose-900/60 shadow-[0_0_20px_-5px_rgba(244,63,94,0.15)]'
                  : 'bg-slate-900/50 border-borderDark/80 hover:border-slate-700'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1.5">
                <div className="flex items-center gap-2">
                  <h4
                    className={`text-sm font-semibold ${
                      isBlocked ? 'text-rose-200 font-bold' : 'text-slate-100'
                    }`}
                  >
                    {evt.title}
                  </h4>
                  {isBlocked && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800 uppercase tracking-wider">
                      Bounded Block
                    </span>
                  )}
                </div>
                <time className="text-[11px] font-mono text-slate-500">{evt.timestamp}</time>
              </div>

              <p
                className={`text-xs leading-relaxed ${
                  isBlocked ? 'text-rose-200/90 font-medium' : 'text-slate-400'
                }`}
              >
                {evt.description}
              </p>

              {isBlocked && (
                <div className="mt-3 pt-2.5 border-t border-rose-900/40 flex items-center gap-1.5 text-xs text-rose-300">
                  <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
                  <span>
                    Zero customer outreach or gateway charges initiated. Bounded safety enforced.
                  </span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
