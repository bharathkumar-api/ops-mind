import './globals.css'
import type { Metadata } from 'next'
import { ReactNode } from 'react'
import Providers from './providers'

export const metadata: Metadata = {
  title: 'OpsMind',
  description: 'Enterprise-safe AIOps platform'
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <header className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">OpsMind</h1>
              <p className="text-sm text-slate-400">RCA-first AIOps control plane</p>
            </div>
            <nav className="flex gap-4 text-sm text-slate-300">
              <a href="/opsmind/incidents" className="hover:text-white">Incidents</a>
              <a href="/opsmind/assistant" className="hover:text-white">Assistant</a>
              <a href="/opsmind/knowledge" className="hover:text-white">Knowledge</a>
            </nav>
          </header>
          <Providers>{children}</Providers>
        </div>
      </body>
    </html>
  )
}
