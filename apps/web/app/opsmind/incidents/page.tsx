'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { listIncidents, createIncident, updateIncidentStatus, type Incident } from '@/lib/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

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
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [title, setTitle] = useState('')
  const [severity, setSeverity] = useState('medium')
  const [description, setDescription] = useState('')
  const queryClient = useQueryClient()

  const { data: incidents = [], isLoading, error } = useQuery({
    queryKey: ['incidents'],
    queryFn: listIncidents,
  })

  const createMutation = useMutation({
    mutationFn: createIncident,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
      setShowCreateForm(false)
      setTitle('')
      setSeverity('medium')
      setDescription('')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateIncidentStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
    },
  })

  const handleCreate = () => {
    if (!title.trim()) return
    createMutation.mutate({
      title: title.trim(),
      severity,
      description: description.trim(),
    })
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'text-red-400 border-red-700'
      case 'high':
        return 'text-orange-400 border-orange-700'
      case 'medium':
        return 'text-yellow-400 border-yellow-700'
      case 'low':
        return 'text-blue-400 border-blue-700'
      default:
        return 'text-slate-400 border-slate-700'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'bg-red-900/30 text-red-300 border-red-700'
      case 'investigating':
        return 'bg-yellow-900/30 text-yellow-300 border-yellow-700'
      case 'resolved':
        return 'bg-green-900/30 text-green-300 border-green-700'
      default:
        return 'bg-slate-900/30 text-slate-300 border-slate-700'
    }
  }

  return (
    <main className="space-y-6">
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Incidents</h2>
            <p className="mt-2 text-slate-300">Review active incidents, signals, and RCA workflows.</p>
          </div>
          <Button onClick={() => setShowCreateForm(!showCreateForm)}>
            {showCreateForm ? 'Cancel' : 'Create Incident'}
          </Button>
        </div>
      </section>

      {showCreateForm && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Incident</h3>
          <div className="space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium mb-2">
                Title
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-600"
                placeholder="Enter incident title"
              />
            </div>
            <div>
              <label htmlFor="severity" className="block text-sm font-medium mb-2">
                Severity
              </label>
              <select
                id="severity"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-600"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label htmlFor="description" className="block text-sm font-medium mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-600"
                rows={3}
                placeholder="Describe the incident"
              />
            </div>
            <Button onClick={handleCreate} disabled={!title.trim() || createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Incident'}
            </Button>
            {createMutation.isError && (
              <p className="text-sm text-red-300">
                Error: {createMutation.error instanceof Error ? createMutation.error.message : 'Failed to create incident'}
              </p>
            )}
          </div>
        </section>
      )}

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h3 className="text-lg font-semibold mb-4">Incident Workspace</h3>
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

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h3 className="text-lg font-semibold mb-4">Active Incidents</h3>
        {isLoading && <p className="text-slate-400">Loading incidents...</p>}
        {error && (
          <p className="text-red-300">
            Error loading incidents: {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        )}
        {!isLoading && !error && incidents.length === 0 && (
          <p className="text-slate-400">No incidents found. Create one to get started.</p>
        )}
        {!isLoading && !error && incidents.length > 0 && (
          <div className="space-y-3">
            {incidents.map((incident: Incident) => (
              <div
                key={incident.id}
                className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 space-y-2"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-slate-100">{incident.title}</h4>
                    {incident.description && (
                      <p className="text-sm text-slate-400 mt-1">{incident.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <span
                      className={`px-2 py-1 rounded text-xs border ${getSeverityColor(incident.severity)}`}
                    >
                      {incident.severity.toUpperCase()}
                    </span>
                    <span
                      className={`px-2 py-1 rounded text-xs border ${getStatusColor(incident.status)}`}
                    >
                      {incident.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2 mt-3">
                  {incident.status === 'open' && (
                    <Button
                      variant="secondary"
                      onClick={() => updateMutation.mutate({ id: incident.id, status: 'investigating' })}
                      disabled={updateMutation.isPending}
                      className="text-xs px-3 py-1"
                    >
                      Mark Investigating
                    </Button>
                  )}
                  {incident.status !== 'resolved' && (
                    <Button
                      variant="secondary"
                      onClick={() => updateMutation.mutate({ id: incident.id, status: 'resolved' })}
                      disabled={updateMutation.isPending}
                      className="text-xs px-3 py-1"
                    >
                      Mark Resolved
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
