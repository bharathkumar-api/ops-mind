export type KGNode = {
  id: string
  label: string
  node_type: string
}

export type KGEdge = {
  id: string
  source_id: string
  target_id: string
  relation: string
}
