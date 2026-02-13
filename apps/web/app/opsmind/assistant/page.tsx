import { Button } from '@/components/ui/button'

export default function AssistantPage() {
  return (
    <main className="space-y-6">
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-xl font-semibold">Assistant</h2>
        <p className="mt-2 text-slate-300">
          Ask OpsMind to correlate evidence and generate RCA narratives with citations.
        </p>
        <div className="mt-4 flex gap-3">
          <Button>Generate RCA summary</Button>
          <Button variant="secondary">Stream response</Button>
        </div>
      </section>
    </main>
  )
}
