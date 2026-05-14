const BASE = '/api'

let _tokenGetter = null
let _onUnauthorized = null

export function setAuthTokenGetter(fn) {
  _tokenGetter = fn
}

export function setOnUnauthorized(fn) {
  _onUnauthorized = fn
}

async function authHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  if (_tokenGetter) {
    const token = _tokenGetter()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

async function apiFetch(path, options = {}) {
  const headers = { ...(await authHeaders()), ...options.headers }
  let res
  try {
    res = await fetch(`${BASE}${path}`, { ...options, headers })
  } catch (e) {
    throw new Error(`Network error: ${e.message}`)
  }
  if (!res.ok) {
    if (res.status === 401 && _onUnauthorized) {
      _onUnauthorized()
    }
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

export async function* streamChat(threadId, message, options = {}) {
  const headers = await authHeaders()
  let res
  try {
    res = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        thread_id: threadId,
        message,
        mode_hint: options.modeHint || null,
        agent_hint: options.agentHint || null,
        return_trace: options.returnTrace ?? true,
      }),
    })
  } catch (e) {
    throw new Error(`Network error: ${e.message}`)
  }

  if (!res.ok) {
    if (res.status === 401 && _onUnauthorized) {
      _onUnauthorized()
    }
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
