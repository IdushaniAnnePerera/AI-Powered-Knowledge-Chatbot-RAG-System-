import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import UploadPanel from './components/UploadPanel'
import DocsList from './components/DocsList'
import Chat from './components/Chat'
import SourcesPanel from './components/SourcesPanel'
import Header from './components/Header'

function randomSession() {
  return crypto.randomUUID ? crypto.randomUUID() : `sess_${Date.now()}`
}

export default function App() {
  const [docs, setDocs] = useState([])
  const [messages, setMessages] = useState([])
  const [sources, setSources] = useState([])
  const [typing, setTyping] = useState(false)
  const [ollamaOk, setOllamaOk] = useState(true)
  const [error, setError] = useState('')

  const sessionId = useMemo(() => {
    const existing = localStorage.getItem('session_id')
    if (existing) return existing
    const id = randomSession()
    localStorage.setItem('session_id', id)
    return id
  }, [])

  const refreshDocs = async () => {
    const data = await api.docs()
    setDocs(data.documents)
  }

  const refreshHealth = async () => {
    try {
      const h = await api.health()
      setOllamaOk(h.ollama_ok)
      if (!h.ollama_ok) setError('Start Ollama: `ollama serve` and `ollama pull llama3.1:8b`.')
      else setError('')
    } catch {
      setOllamaOk(false)
      setError('Backend unavailable')
    }
  }

  useEffect(() => {
    refreshDocs()
    refreshHealth()
    api.history(sessionId).then((h) => setMessages(h.messages)).catch(() => {})
  }, [sessionId])

  const onUpload = async (file) => {
    try {
      await api.upload(file)
      refreshDocs()
    } catch (e) {
      setError(e.message)
    }
  }

  const onDeleteDoc = async (id) => {
    try {
      await api.deleteDoc(id)
      refreshDocs()
    } catch (e) {
      setError(e.message)
    }
  }

  const onSend = async (message) => {
    setTyping(true)
    setMessages((m) => [...m, { role: 'user', content: message }])
    try {
      const res = await api.chat({ session_id: sessionId, message })
      setMessages((m) => [...m, { role: 'assistant', content: res.answer }])
      setSources(res.sources)
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', content: `Error: ${e.message}` }])
    } finally {
      setTyping(false)
    }
  }

  const onClear = async () => {
    await api.clearChat(sessionId)
    setMessages([])
    setSources([])
  }

  return (
    <div className="h-screen flex flex-col">
      <Header ollamaOk={ollamaOk} error={error} />
      <div className="flex-1 grid grid-cols-12 min-h-0">
        <aside className="col-span-3 border-r bg-slate-50 flex flex-col min-h-0">
          <UploadPanel onUpload={onUpload} />
          <DocsList docs={docs} onDelete={onDeleteDoc} />
        </aside>
        <main className="col-span-6 min-h-0">
          <Chat messages={messages} onSend={onSend} typing={typing} onClear={onClear} />
        </main>
        <aside className="col-span-3 border-l bg-slate-50 min-h-0">
          <SourcesPanel sources={sources} />
        </aside>
      </div>
    </div>
  )
}
