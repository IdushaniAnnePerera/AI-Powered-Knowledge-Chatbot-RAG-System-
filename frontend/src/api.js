const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function req(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, options)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}

export const api = {
  health: () => req('/health'),
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return req('/upload', { method: 'POST', body: fd })
  },
  docs: () => req('/docs'),
  deleteDoc: (docId) => req(`/docs/${docId}`, { method: 'DELETE' }),
  chat: (payload) => req('/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  history: (sessionId) => req(`/chat/${sessionId}`),
  clearChat: (sessionId) => req(`/chat/${sessionId}`, { method: 'DELETE' }),
}
