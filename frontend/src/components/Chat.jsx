import { useState } from 'react'

export default function Chat({ messages, onSend, typing, onClear }) {
  const [text, setText] = useState('')

  const submit = async () => {
    if (!text.trim()) return
    const msg = text
    setText('')
    await onSend(msg)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-3 border-b bg-white">
        <h2 className="font-semibold">Chat</h2>
        <button onClick={onClear} className="text-sm text-slate-600 hover:underline">Clear chat</button>
      </div>
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`max-w-[85%] p-3 rounded ${m.role === 'user' ? 'bg-blue-600 text-white ml-auto' : 'bg-white border'}`}>
            {m.content}
          </div>
        ))}
        {typing && <div className="text-sm text-slate-500">Assistant is typing...</div>}
      </div>
      <div className="p-3 border-t bg-white">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="Ask from your uploaded documents..."
          className="w-full border rounded px-3 py-2"
        />
      </div>
    </div>
  )
}
