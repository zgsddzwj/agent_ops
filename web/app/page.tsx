import { PageHeader, StatCard } from "@/components/layout";
import { fetchApi } from "@/lib/api";

async function getOverview() {
  try {
    const projects = await fetchApi<{ id: string; name: string }[]>("/v1/projects");
    return { projects, error: null };
  } catch {
    return { projects: [], error: "API unavailable - start backend with docker compose up" };
  }
}

export default async function OverviewPage() {
  const { projects, error } = await getOverview();

  return (
    <div>
      <PageHeader title="Overview" />
      {error && (
        <div className="mb-4 rounded-md border border-yellow-600/50 bg-yellow-600/10 p-3 text-sm text-yellow-300">
          {error}
        </div>
      )}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Projects" value={String(projects.length)} sub="Registered ai_projects" />
        <StatCard label="Today's Cost" value="$0.00" sub="Connect API key for live data" />
        <StatCard label="P95 Latency" value="—" sub="ms" />
        <StatCard label="Error Rate" value="0%" sub="Last 24h" />
      </div>
      <div className="mt-8 card">
        <h2 className="mb-4 text-lg font-semibold">Quick Start</h2>
        <pre className="overflow-x-auto rounded bg-black/30 p-4 text-sm text-green-300">
{`# Initialize external ai_project
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
