import { PageHeader, StatCard } from "@/components/layout";
import { fetchApi, ApiError } from "@/lib/api";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Overview - AgentOps",
  description: "AgentOps dashboard overview with real-time metrics",
};

interface Project {
  id: string;
  name: string;
}

interface MetricsSummary {
  total_runs: number;
  total_tokens: number;
  total_cost_usd: number;
  error_rate: number;
  p95_latency_ms: number | null;
}

async function getOverview() {
  try {
    const [projects, metrics] = await Promise.all([
      fetchApi<Project[]>("/v1/projects"),
      fetchApi<MetricsSummary>("/v1/metrics/summary?hours=24").catch(() => null),
    ]);
    return { projects, metrics, error: null };
  } catch (err) {
    if (err instanceof ApiError) {
      return {
        projects: [],
        metrics: null,
        error: err.status === 0
          ? "API unavailable - start backend with docker compose up"
          : `API error: ${err.message}`,
      };
    }
    return { projects: [], metrics: null, error: "An unexpected error occurred" };
  }
}

export default async function OverviewPage() {
  const { projects, metrics, error } = await getOverview();

  const todayCost = metrics?.total_cost_usd
    ? `$${metrics.total_cost_usd.toFixed(2)}`
    : "$0.00";
  const p95Latency = metrics?.p95_latency_ms
    ? `${Math.round(metrics.p95_latency_ms)}`
    : "—";
  const errorRate = metrics?.error_rate != null
    ? `${(metrics.error_rate * 100).toFixed(1)}%`
    : "0%";

  return (
    <div>
      <PageHeader title="Overview" />
      {error && (
        <div className="mb-4 rounded-md border border-yellow-600/50 bg-yellow-600/10 p-3 text-sm text-yellow-300">
          ⚠️ {error}
        </div>
      )}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Projects" value={String(projects.length)} sub="Registered projects" />
        <StatCard label="Today&apos;s Cost" value={todayCost} sub="Last 24h token spend" />
        <StatCard label="P95 Latency" value={p95Latency} sub="ms" />
        <StatCard
          label="Error Rate"
          value={errorRate}
          sub="Last 24h"
          valueClassName={parseFloat(errorRate) > 5 ? "text-red-400" : undefined}
        />
      </div>
      <div className="mt-8 card">
        <h2 className="mb-4 text-lg font-semibold">Quick Start</h2>
        <pre className="overflow-x-auto rounded bg-black/30 p-4 text-sm text-green-300">
{`# Initialize your project
agent-ops init ./my-agent
agent-ops link ./my-agent

# Run evaluations
agent-ops eval run --project ./my-agent --suite smoke
agent-ops benchmark run --project ./my-agent --preset cost_efficient
agent-ops security scan --project ./my-agent`}
        </pre>
      </div>
    </div>
  );
}
