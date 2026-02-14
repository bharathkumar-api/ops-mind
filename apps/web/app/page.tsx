import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="space-y-6">
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-xl font-semibold">Welcome to OpsMind</h2>
        <p className="mt-2 text-slate-300">
          Navigate to incidents, assistant, and governance modules using the navigation above.
        </p>
      </section>
      
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/opsmind/assistant">
            <div className="rounded-lg border border-slate-700 p-4 hover:bg-slate-800/50 transition-colors cursor-pointer">
              <h4 className="font-semibold mb-2">Assistant</h4>
              <p className="text-sm text-slate-400">Ask OpsMind to generate RCA narratives and correlate evidence</p>
            </div>
          </Link>
          <Link href="/opsmind/incidents">
            <div className="rounded-lg border border-slate-700 p-4 hover:bg-slate-800/50 transition-colors cursor-pointer">
              <h4 className="font-semibold mb-2">Incidents</h4>
              <p className="text-sm text-slate-400">Review active incidents, signals, and RCA workflows</p>
            </div>
          </Link>
          <Link href="/opsmind/knowledge">
            <div className="rounded-lg border border-slate-700 p-4 hover:bg-slate-800/50 transition-colors cursor-pointer">
              <h4 className="font-semibold mb-2">Knowledge Base</h4>
              <p className="text-sm text-slate-400">Manage and search knowledge documents</p>
            </div>
          </Link>
          <Link href="/opsmind/governance/audit">
            <div className="rounded-lg border border-slate-700 p-4 hover:bg-slate-800/50 transition-colors cursor-pointer">
              <h4 className="font-semibold mb-2">Audit Log</h4>
              <p className="text-sm text-slate-400">View audit events and compliance logs</p>
            </div>
          </Link>
        </div>
      </section>
    </main>
  )
}
