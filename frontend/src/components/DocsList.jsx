export default function DocsList({ docs, onDelete }) {
  return (
    <div className="p-4 overflow-auto">
      <h2 className="font-semibold mb-2">Documents</h2>
      <ul className="space-y-2">
        {docs.map((doc) => (
          <li key={doc.id} className="bg-white p-2 rounded border text-sm flex justify-between items-center gap-2">
            <span className="truncate">{doc.filename}</span>
            <button onClick={() => onDelete(doc.id)} className="text-red-600 hover:underline">Delete</button>
          </li>
        ))}
      </ul>
      {docs.length === 0 && <p className="text-sm text-slate-500">No documents uploaded.</p>}
    </div>
  )
}
