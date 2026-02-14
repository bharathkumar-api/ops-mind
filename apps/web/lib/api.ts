const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Helper function to get auth headers (for endpoints that require auth)
function getAuthHeaders(): HeadersInit {
  // In dev mode with DEV_AUTH_BYPASS, we still need to send a Bearer token
  // The backend will accept any token when DEV_AUTH_BYPASS is true
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer dev-token',
  }
}

export interface ChatSendRequest {
  message: string
  conversation_id?: string | null
  org_id?: string | null
  project_id?: string | null
  context_overrides?: Record<string, unknown>
}

export interface ResponseModel {
  primary_text: string
  status: string
  hypotheses?: Array<{ statement: string; confidence: number }>
  evidence?: Array<{ ref_type: string; description: string }>
  next_actions?: string[]
  followup_questions?: string[]
  async_job_id?: string | null
}

export interface ChatSendResponse {
  conversation_id: string
  response: ResponseModel
}

export async function sendChatMessage(request: ChatSendRequest): Promise<ChatSendResponse> {
  const response = await fetch(`${API_URL}/v1/chat/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: request.message,
      conversation_id: request.conversation_id || null,
      org_id: request.org_id || 'local-org',
      project_id: request.project_id || 'local-project',
      context_overrides: request.context_overrides || {},
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API error: ${response.status} - ${error}`)
  }

  return response.json()
}

// Incidents API
export interface Incident {
  id: string
  title: string
  status: string
  severity: string
  description?: string
}

export interface IncidentCreate {
  title: string
  severity: string
  description?: string
}

export async function listIncidents(): Promise<Incident[]> {
  const response = await fetch(`${API_URL}/opsmind/incidents/`, {
    method: 'GET',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API error: ${response.status} - ${error}`)
  }

  return response.json()
}

export async function createIncident(payload: IncidentCreate): Promise<{ id: string }> {
  const response = await fetch(`${API_URL}/opsmind/incidents/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API error: ${response.status} - ${error}`)
  }

  return response.json()
}

export async function updateIncidentStatus(
  incidentId: string,
  status: string
): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/opsmind/incidents/${incidentId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({ status }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API error: ${response.status} - ${error}`)
  }

  return response.json()
}

// Knowledge Base API
export interface KBDocument {
  id: string
  title: string
  content: string
}

export interface KBDocumentCreate {
  title: string
  content: string
}

export async function listKBDocuments(): Promise<KBDocument[]> {
  const response = await fetch(`${API_URL}/opsmind/knowledge/documents`, {
    method: 'GET',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API error: ${response.status} - ${error}`)
  }

  return response.json()
}

export async function createKBDocument(payload: KBDocumentCreate): Promise<{ id: string }> {
  const response = await fetch(`${API_URL}/opsmind/knowledge/documents`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API error: ${response.status} - ${error}`)
  }

  return response.json()
}
