export type RCAReport = {
  id: string
  incident_id: string
  summary: string
  evidence: Array<{ source: string; detail: string }>
  approved: boolean
}
