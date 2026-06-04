import Link from "next/link";
import { PageHeader } from "@/components/layout";

export default function BenchmarksPage() {
  return (
    <div>
      <PageHeader title="Model Benchmarks">
        <button className="btn">+ New Benchmark</button>
      </PageHeader>
      <div className="card mb-4">
        <p className="text-[var(--muted)]">
          Compare OpenAI, Qwen, DeepSeek models:{" "}
          <code className="text-indigo-300">agent-ops benchmark run --project ./ai_project --preset domestic</code>
        </p>
      </div>
      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="border-b border-[var(--border)] bg-black/20">
            <tr>
              <th className="px-4 py-3 text-left">Model</th>
              <th className="px-4 py-3 text-right">TTFT P50</th>
              <th className="px-4 py-3 text-right">E2E P50</th>
              <th className="px-4 py-3 text-right">E2E P95</th>
              <th className="px-4 py-3 text-right">Avg Cost</th>
              <th className="px-4 py-3 text-right">Quality</th>
            </tr>
          </thead>
          <tbody>
            <tr className="table-row">
              <td className="px-4 py-3 font-medium text-indigo-300">qwen:qwen-turbo</td>
              <td className="px-4 py-3 text-right text-green-400">120ms</td>
              <td className="px-4 py-3 text-right">480ms</td>
              <td className="px-4 py-3 text-right">720ms</td>
              <td className="px-4 py-3 text-right">$0.001</td>
              <td className="px-4 py-3 text-right">0.85</td>
            </tr>
            <tr className="table-row">
              <td className="px-4 py-3 font-medium text-indigo-300">openai:gpt-4o</td>
              <td className="px-4 py-3 text-right">280ms</td>
              <td className="px-4 py-3 text-right">920ms</td>
              <td className="px-4 py-3 text-right">1400ms</td>
              <td className="px-4 py-3 text-right">$0.012</td>
              <td className="px-4 py-3 text-right text-green-400">0.95</td>
            </tr>
            <tr className="table-row">
              <td className="px-4 py-3 font-medium text-indigo-300">deepseek:deepseek-chat</td>
              <td className="px-4 py-3 text-right">150ms</td>
              <td className="px-4 py-3 text-right">550ms</td>
              <td className="px-4 py-3 text-right">850ms</td>
              <td className="px-4 py-3 text-right text-green-400">$0.0008</td>
              <td className="px-4 py-3 text-right">0.88</td>
            </tr>
          </tbody>
        </table>
        <p className="px-4 py-3 text-xs text-[var(--muted)]">Sample data — run benchmark CLI to populate real results</p>
      </div>
    </div>
  );
}
