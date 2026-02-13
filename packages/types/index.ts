export type OrgScoped = {
  org_id: string
}

export type Incident = OrgScoped & {
  id: string
  title: string
  status: string
  severity: string
  description: string
}
