import { PageHeader } from "@/components/layout";
import { fetchApi } from "@/lib/api";

export default async function ProjectsPage() {
  let projects: { id: string; name: string; entrypoint: string | null; api_key_prefix: string; created_at: string }[] = [];
  try {
    projects = await fetchApi("/v1/projects");
  } catch {
    // empty
  }

  return (
    <div>
      <PageHeader title="Projects" />
      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="border-b border-[var(--border)] bg-black/20">
            <tr>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Entrypoint</th>
              <th className="px-4 py-3 text-left">API Key Prefix</th>
              <th className="px-4 py-3 text-left">Created</th>
              <th className="px-4 py-3 text-left">SDK Snippet</th>
            </tr>
          </thead>
          <tbody>
            {projects.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-[var(--muted)]">
                  No projects registered. Run: agent-ops link ./your-ai-project
                </td>
              </tr>
            ) : (
              projects.map((p) => (
                <tr key={p.id} className="table-row">
                  <td className="px-4 py-3 font-medium">{p.name}</td>
                  <td className="px-4 py-3 text-[var(--muted)]">{p.entrypoint || "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs">{p.api_key_prefix}...</td>
                  <td className="px-4 py-3">{new Date(p.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <code className="text-xs text-indigo-300">AgentOpsCallbackHandler(client)</code>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
