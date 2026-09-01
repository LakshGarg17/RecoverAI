import type { Metadata } from 'next';
import './globals.css';
import { DashboardLayout } from '../components/DashboardLayout';

export const metadata: Metadata = {
  title: 'RecoverAI — Autonomous Revenue Recovery Agent',
  description: 'AI-Powered Autonomous Revenue Recovery & Intelligent Dunning Platform for E-Commerce.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-background selection:bg-indigo-500 selection:text-white">
        <DashboardLayout>
          {children}
        </DashboardLayout>
      </body>
    </html>
  );
}

