import { PageHeader } from "@/components/layout";

export default function SecurityPage() {
  return (
    <div>
      <PageHeader title="Security Scans" />
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card"><div className="text-sm text-[var(--muted)]">Last Pass Rate</div><div className="text-2xl font-semibold text-green-400">—</div></div>
        <div className="card"><div className="text-sm text-[var(--muted)]">Critical Findings</div><div className="text-2xl font-semibold">0</div></div>
        <div className="card"><div className="text-sm text-[var(--muted)]">Scans (30d)</div><div className="text-2xl font-semibold">0</div></div>
      </div>
      <div className="card">
        <h2 className="mb-4 font-semibold">Test Suites</h2>
        <ul className="space-y-2 text-sm">
          <li className="flex justify-between rounded border border-[var(--border)] p-3">
            <span>Prompt Injection</span>
            <code className="text-indigo-300">agent-ops security scan --suite prompt_injection</code>
          </li>
          <li className="flex justify-between rounded border border-[var(--border)] p-3">
            <span>Jailbreak</span>
            <code className="text-indigo-300">agent-ops security scan --suite jailbreak</code>
          </li>
        </ul>
      </div>
    </div>
  );
}
