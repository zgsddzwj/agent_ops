import { PageHeader } from "@/components/layout";

export default function EvalsPage() {
  return (
    <div>
      <PageHeader title="Evaluations">
        <button className="btn">+ New Eval Run</button>
      </PageHeader>
      <div className="card">
        <p className="mb-4 text-[var(--muted)]">
          Run evaluations via CLI: <code className="text-indigo-300">agent-ops eval run --project ./ai_project --suite regression</code>
        </p>
        <table className="w-full text-sm">
          <thead className="border-b border-[var(--border)]">
            <tr>
              <th className="px-4 py-2 text-left">Suite</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Pass Rate</th>
              <th className="px-4 py-2 text-left">Created</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-[var(--muted)]">
                No eval runs yet. Use CLI with API key to upload results.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
