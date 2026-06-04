import { PageHeader } from "@/components/layout";
import { fetchApi } from "@/lib/api";

export default async function TraceDetailPage({ params }: { params: { id: string } }) {
  let run = null;
  let spans: { id: string; span_type: string; name: string | null; latency_ms: number | null; ttft_ms: number | null; model: string | null; status: string }[] = [];

  try {
    run = await fetchApi(`/v1/runs/${params.id}`);
    spans = await fetchApi(`/v1/runs/${params.id}/spans`);
  } catch {
    // empty
  }

  return (
    <div>
      <PageHeader title={`Trace ${params.id.slice(0, 8)}...`} />
      {run && (
        <div className="mb-4 grid grid-cols-4 gap-4">
          <div className="card"><div className="text-sm text-[var(--muted)]">Status</div><div>{run.status}</div></div>
          <div className="card"><div className="text-sm text-[var(--muted)]">Latency</div><div>{run.latency_ms ? `${run.latency_ms.toFixed(0)}ms` : "—"}</div></div>
          <div className="card"><div className="text-sm text-[var(--muted)]">TTFT</div><div>{run.ttft_ms ? `${run.ttft_ms.toFixed(0)}ms` : "—"}</div></div>
          <div className="card"><div className="text-sm text-[var(--muted)]">Cost</div><div>{run.cost_usd ? `$${run.cost_usd.toFixed(4)}` : "—"}</div></div>
        </div>
      )}
      <div className="card">
        <h2 className="mb-4 font-semibold">Span Waterfall</h2>
        {spans.length === 0 ? (
          <p className="text-[var(--muted)]">No spans recorded</p>
        ) : (
          <div className="space-y-2">
            {spans.map((span) => (
              <div key={span.id} className="flex items-center gap-4 rounded border border-[var(--border)] p-3">
                <span className="w-16 rounded bg-indigo-600/20 px-2 py-0.5 text-xs text-indigo-300">{span.span_type}</span>
                <span className="flex-1">{span.name || span.span_type}</span>
                {span.model && <span className="text-xs text-[var(--muted)]">{span.model}</span>}
                {span.ttft_ms && <span className="text-xs text-green-400">TTFT {span.ttft_ms.toFixed(0)}ms</span>}
                {span.latency_ms && <span className="text-xs">{span.latency_ms.toFixed(0)}ms</span>}
                <span className={span.status === "success" ? "text-green-400" : "text-red-400"}>{span.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
