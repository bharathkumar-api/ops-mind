'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { listKBDocuments, createKBDocument, type KBDocument } from '@/lib/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export default function KnowledgePage() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const queryClient = useQueryClient()

  const { data: documents = [], isLoading, error } = useQuery({
    queryKey: ['kb-documents'],
    queryFn: listKBDocuments,
  })

  const createMutation = useMutation({
    mutationFn: createKBDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb-documents'] })
      setShowCreateForm(false)
      setTitle('')
      setContent('')
    },
  })

  const handleCreate = () => {
    if (!title.trim() || !content.trim()) return
    createMutation.mutate({
      title: title.trim(),
      content: content.trim(),
    })
  }

  return (
    <main className="space-y-6">
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Knowledge Base</h2>
            <p className="mt-2 text-slate-300">Curate runbooks and RCA documentation for grounding.</p>
          </div>
          <Button onClick={() => setShowCreateForm(!showCreateForm)}>
            {showCreateForm ? 'Cancel' : 'Add Document'}
          </Button>
        </div>
      </section>

      {showCreateForm && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Document</h3>
          <div className="space-y-4">
            <div>
              <label htmlFor="doc-title" className="block text-sm font-medium mb-2">
                Title
              </label>
              <input
                id="doc-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-600"
                placeholder="Enter document title"
              />
            </div>
            <div>
              <label htmlFor="doc-content" className="block text-sm font-medium mb-2">
                Content
              </label>
              <textarea
                id="doc-content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-600 resize-y min-h-[200px]"
                rows={10}
                placeholder="Enter document content (markdown supported)"
              />
            </div>
            <Button
              onClick={handleCreate}
              disabled={!title.trim() || !content.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Document'}
            </Button>
            {createMutation.isError && (
              <p className="text-sm text-red-300">
                Error: {createMutation.error instanceof Error ? createMutation.error.message : 'Failed to create document'}
              </p>
            )}
          </div>
        </section>
      )}

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h3 className="text-lg font-semibold mb-4">Documents</h3>
        {isLoading && <p className="text-slate-400">Loading documents...</p>}
        {error && (
          <p className="text-red-300">
            Error loading documents: {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        )}
        {!isLoading && !error && documents.length === 0 && (
          <p className="text-slate-400">No documents found. Create one to get started.</p>
        )}
        {!isLoading && !error && documents.length > 0 && (
          <div className="space-y-4">
            {documents.map((doc: KBDocument) => (
              <div
                key={doc.id}
                className="rounded-lg border border-slate-700 bg-slate-900/50 p-4"
              >
                <h4 className="font-semibold text-slate-100 mb-2">{doc.title}</h4>
                <div className="text-sm text-slate-300 whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {doc.content}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
