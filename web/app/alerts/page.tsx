import { PageHeader } from "@/components/layout";

export default function AlertsPage() {
  return (
    <div>
      <PageHeader title="Alerts">
        <button className="btn">+ New Rule</button>
      </PageHeader>
      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <h2 className="mb-4 font-semibold">Alert Rules</h2>
          <div className="space-y-2 text-sm">
            <div className="rounded border border-[var(--border)] p-3">
              <div className="font-medium">Cost Threshold</div>
              <div className="text-[var(--muted)]">Alert when hourly cost &gt; $10</div>
            </div>
            <div className="rounded border border-[var(--border)] p-3">
              <div className="font-medium">P95 Latency SLO</div>
              <div className="text-[var(--muted)]">Alert when P95 latency &gt; 2000ms</div>
            </div>
            <div className="rounded border border-[var(--border)] p-3">
              <div className="font-medium">Security Pass Rate</div>
              <div className="text-[var(--muted)]">Alert when pass rate &lt; 95%</div>
            </div>
          </div>
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">Recent Events</h2>
          <p className="text-[var(--muted)]">No alert events triggered yet.</p>
        </div>
      </div>
    </div>
  );
}
