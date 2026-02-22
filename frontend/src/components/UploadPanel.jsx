import { useState } from 'react'

export default function UploadPanel({ onUpload }) {
  const [busy, setBusy] = useState(false)

  const handleChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy(true)
    await onUpload(file).finally(() => setBusy(false))
    e.target.value = ''
  }

  return (
    <div className="p-4 border-b">
      <label className="block text-sm font-semibold mb-2">Upload PDF/TXT/MD</label>
      <input
        disabled={busy}
        type="file"
        accept=".pdf,.txt,.md"
        onChange={handleChange}
        className="w-full text-sm"
      />
      {busy && <p className="text-xs text-slate-500 mt-2">Uploading...</p>}
    </div>
  )
}
