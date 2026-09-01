'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  RefreshCw,
  Sparkles,
  Receipt,
  ShieldCheck,
  FileText,
  Settings,
  CreditCard,
  Zap,
} from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { label: 'Overview', href: '/', icon: LayoutDashboard },
    { label: 'Recovery Opportunities', href: '/recovery', icon: RefreshCw },
    { label: 'AI Insights', href: '/ai-insights', icon: Sparkles },
    { label: 'Transactions', href: '/transactions', icon: Receipt },
    { label: 'Guardrails & Policy', href: '/guardrails', icon: ShieldCheck },
    { label: 'Audit Log', href: '/audit', icon: FileText },
    { label: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-surface/95 border-r border-borderDark/80 flex flex-col justify-between shrink-0 min-h-screen">
      <div>
        {/* Brand Logo */}
        <div className="h-16 flex items-center px-6 border-b border-borderDark/80">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary-600 to-indigo-400 flex items-center justify-center text-white shadow-neon group-hover:scale-105 transition-transform">
              <Zap className="w-4 h-4 fill-white" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white font-heading">
                Recover<span className="text-primary-400">AI</span>
              </span>
              <span className="block text-[10px] text-slate-500 font-mono -mt-1">
                Autonomous Dunning Agent
              </span>
            </div>
          </Link>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1">
          <div className="px-3 py-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Main Menu
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === '/'
                ? pathname === '/' || pathname === '/dashboard'
                : pathname?.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-primary-600/15 text-primary-400 font-semibold border border-primary-500/30 shadow-neon'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-primary-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Gateway Environment Badge */}
      <div className="p-4 m-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">Gateway</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-950 text-amber-400 border border-amber-800/60">
            Test Mode
          </span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5 flex items-center gap-1">
          <CreditCard className="w-3 h-3 text-indigo-400" />
          Razorpay Test Mode Active
        </p>
      </div>
    </aside>
  );
}
