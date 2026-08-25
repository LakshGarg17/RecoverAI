import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'RecoverAI — Autonomous Payment Recovery Agent',
  description: 'AI-Powered Autonomous Payment Recovery & Intelligent Dunning Platform for Modern SaaS and Enterprises.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
