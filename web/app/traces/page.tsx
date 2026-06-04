import Link from "next/link";
import { PageHeader } from "@/components/layout";
import { fetchApi } from "@/lib/api";

export default async function TracesPage() {
  let runs: { id: string; name: string | null; status: string; latency_ms: number | null; cost_usd: number | null; created_at: string }[] = [];
  try {
    runs = await fetchApi("/v1/runs");
  } catch {
    // no auth - show empty
  }

  return (
    <div>
      <PageHeader title="Trace Explorer" />
      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="border-b border-[var(--border)] bg-black/20">
            <tr>
              <th className="px-4 py-3 text-left">Run ID</th>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-right">Latency</th>
              <th className="px-4 py-3 text-right">Cost</th>
              <th className="px-4 py-3 text-left">Created</th>
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-[var(--muted)]">
                  No traces yet. Embed SDK in your ai_project to start collecting.
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <tr key={run.id} className="table-row">
                  <td className="px-4 py-3">
                    <Link href={`/traces/${run.id}`} className="text-indigo-400 hover:underline">
                      {run.id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="px-4 py-3">{run.name || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={run.status === "success" ? "text-green-400" : run.status === "error" ? "text-red-400" : "text-yellow-400"}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">{run.latency_ms ? `${run.latency_ms.toFixed(0)}ms` : "—"}</td>
                  <td className="px-4 py-3 text-right">{run.cost_usd ? `$${run.cost_usd.toFixed(4)}` : "—"}</td>
                  <td className="px-4 py-3">{new Date(run.created_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
