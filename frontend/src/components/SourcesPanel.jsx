export default function SourcesPanel({ sources }) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b bg-white">
        <h2 className="font-semibold">Sources</h2>
      </div>
      <div className="p-3 overflow-auto space-y-2">
        {sources.map((s) => (
          <div key={s.chunk_id} className="bg-white border rounded p-2 text-xs">
            <div className="font-semibold">{s.filename}</div>
            <div>doc_id: {s.doc_id}</div>
            <div>page: {s.page_number ?? 'N/A'}</div>
            <div>chunk: {s.chunk_id}</div>
            <p className="mt-1 text-slate-600">{s.snippet}...</p>
          </div>
        ))}
        {sources.length === 0 && <p className="text-sm text-slate-500">No sources yet.</p>}
      </div>
    </div>
  )
}
