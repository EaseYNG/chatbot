const BASE = '/api'

async function apiFetch(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, options)
  } catch (e) {
    throw new Error(`Network error: ${e.message}`)
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res
}

export async function fetchConversations() {
  const res = await apiFetch('/conversations')
  return res.json()
}

export async function fetchConversation(id) {
  const res = await apiFetch(`/conversations/${id}`)
  return res.json()
}

export async function deleteConversation(id) {
  const res = await apiFetch(`/conversations/${id}`, { method: 'DELETE' })
  return res.json()
}

export async function* streamChat(threadId, message) {
  let res
  try {
    res = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, message }),
    })
  } catch (e) {
    throw new Error(`Network error: ${e.message}`)
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || 'Chat request failed')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentEvent = null
    for (const line of lines) {
      const trimmed = line.replace(/\r$/, '')
      if (trimmed.startsWith('event: ')) {
        currentEvent = trimmed.slice(7)
      } else if (trimmed.startsWith('data: ') && currentEvent) {
        const raw = trimmed.slice(6)
        try {
          const data = JSON.parse(raw)
          yield { type: currentEvent, ...data }
        } catch {
          // skip unparseable
        }
        currentEvent = null
      }
    }
  }
}
