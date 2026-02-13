export type AuditEvent = {
  id: string
  event_type: string
  detail: Record<string, unknown>
  created_at: string
}
