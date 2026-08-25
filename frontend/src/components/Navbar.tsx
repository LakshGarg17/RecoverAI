import React from 'react';
import { ShieldAlert, Activity, Sparkles, BookOpen, Layers } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="w-full border-b border-borderDark/80 bg-surface/50 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-primary-500 to-cyan-400 flex items-center justify-center shadow-neon">
            <ShieldAlert className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-heading font-extrabold text-xl tracking-tight text-white">
                Recover<span className="text-primary-400">AI</span>
              </span>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full bg-primary-500/20 text-primary-300 border border-primary-500/30">
                Day 1 Architecture
              </span>
            </div>
            <p className="text-xs text-gray-400 font-medium">Autonomous Payment Recovery Agent</p>
          </div>
        </div>

        {/* Action Links */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-300 hover:text-white bg-surface hover:bg-surfaceHover border border-borderDark transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5 text-primary-400" />
            <span className="hidden sm:inline">API Docs (Swagger)</span>
            <span className="sm:hidden">Docs</span>
          </a>

          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block mr-1"></span>
            <span>Local Dev</span>
          </div>
        </div>
      </div>
    </header>
  );
};
