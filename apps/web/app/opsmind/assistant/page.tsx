'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { sendChatMessage, type ChatSendResponse } from '@/lib/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function AssistantPage() {
  const [message, setMessage] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const sendMutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: (data: ChatSendResponse) => {
      setConversationId(data.conversation_id)
      setMessage('')
      queryClient.invalidateQueries({ queryKey: ['conversation', data.conversation_id] })
    },
  })

  const handleSend = () => {
    if (!message.trim()) return
    sendMutation.mutate({
      message: message.trim(),
      conversation_id: conversationId,
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <main className="space-y-6">
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-xl font-semibold">Assistant</h2>
        <p className="mt-2 text-slate-300">
          Ask OpsMind to correlate evidence and generate RCA narratives with citations.
        </p>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="message" className="block text-sm font-medium mb-2">
              Describe your incident or question
            </label>
            <textarea
              id="message"
              name="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Example: Database connection timeout occurred at 2:30 PM. Multiple services are affected..."
              className="w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-600 focus:border-slate-600 resize-y min-h-[100px]"
              rows={4}
              autoFocus
            />
          </div>
          <div className="flex gap-3">
            <Button 
              onClick={handleSend}
              disabled={!message.trim() || sendMutation.isPending}
            >
              {sendMutation.isPending ? 'Sending...' : 'Send Message'}
            </Button>
            {conversationId && (
              <Button 
                variant="secondary"
                onClick={() => {
                  setConversationId(null)
                  setMessage('')
                }}
              >
                New Conversation
              </Button>
            )}
          </div>
        </div>
      </section>

      {sendMutation.isError && (
        <section className="rounded-xl border border-red-800 bg-red-900/20 p-4">
          <p className="text-sm text-red-300">
            Error: {sendMutation.error instanceof Error ? sendMutation.error.message : 'Failed to send message'}
          </p>
        </section>
      )}

      {sendMutation.isSuccess && sendMutation.data && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
          <h3 className="text-lg font-semibold">Response</h3>
          <div className="text-slate-200 whitespace-pre-wrap">
            {sendMutation.data.response.primary_text}
          </div>
          
          {sendMutation.data.response.status && (
            <div className="text-sm">
              <span className="text-slate-400">Status: </span>
              <span className="text-slate-200">{sendMutation.data.response.status}</span>
            </div>
          )}

          {sendMutation.data.response.hypotheses && sendMutation.data.response.hypotheses.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Hypotheses</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {sendMutation.data.response.hypotheses.map((h, i) => (
                  <li key={i}>
                    {h.statement} ({Math.round(h.confidence * 100)}%)
                  </li>
                ))}
              </ul>
            </div>
          )}

          {sendMutation.data.response.evidence && sendMutation.data.response.evidence.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Evidence</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {sendMutation.data.response.evidence.map((e, i) => (
                  <li key={i}>
                    <span className="font-mono text-xs text-slate-400">{e.ref_type}:</span> {e.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {sendMutation.data.response.next_actions && sendMutation.data.response.next_actions.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Next Actions</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {sendMutation.data.response.next_actions.map((action, i) => (
                  <li key={i}>{action}</li>
                ))}
              </ul>
            </div>
          )}

          {sendMutation.data.response.followup_questions && sendMutation.data.response.followup_questions.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Follow-up Questions</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {sendMutation.data.response.followup_questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </main>
  )
}
