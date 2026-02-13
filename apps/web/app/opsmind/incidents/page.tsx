const tabs = [
  'Overview',
  'Detect',
  'Correlate',
  'Impact',
  'Remedy',
  'Approvals',
  'Actions',
  'Rollback',
  'RCA',
  'Assistant'
]

export default function IncidentsPage() {
  return (
    <main className="space-y-6">
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-xl font-semibold">Incidents</h2>
        <p className="mt-2 text-slate-300">Review active incidents, signals, and RCA workflows.</p>
      </section>
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h3 className="text-lg font-semibold">Incident Workspace</h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <span
              key={tab}
              className="rounded-full border border-slate-700 px-3 py-1 text-xs uppercase tracking-wide text-slate-300"
            >
              {tab}
            </span>
          ))}
        </div>
      </section>
    </main>
  )
}
