export default function Header({ ollamaOk, error }) {
  return (
    <header className="p-3 bg-slate-900 text-white flex items-center justify-between">
      <h1 className="font-bold">AI-Powered Knowledge Chatbot (Local RAG)</h1>
      <div className="text-sm">
        {!ollamaOk && <span className="bg-red-600 px-2 py-1 rounded">Ollama Offline</span>}
        {error && <span className="ml-2 text-red-300">{error}</span>}
      </div>
    </header>
  )
}
