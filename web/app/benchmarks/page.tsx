import Link from "next/link";
import { PageHeader } from "@/components/layout";
import { fetchApi } from "@/lib/api";

type BenchmarkResult = {
  id: string;
  model_name: string;
  provider: string;
  dataset: string;
  ttft_p50: number;
  ttft_p95: number;
  e2e_p50: number;
  e2e_p95: number;
  avg_cost: number;
  quality_score: number;
  tokens_in: number;
  tokens_out: number;
  runs: number;
  created_at: string;
  status: string;
};

// Demo data for display when no real data is available
const DEMO_BENCHMARKS: BenchmarkResult[] = [
  {
    id: "demo-1",
    model_name: "qwen-turbo",
    provider: "qwen",
    dataset: "smoke",
    ttft_p50: 120,
    ttft_p95: 240,
    e2e_p50: 480,
    e2e_p95: 720,
    avg_cost: 0.001,
    quality_score: 0.85,
    tokens_in: 850,
    tokens_out: 420,
    runs: 25,
    created_at: new Date().toISOString(),
    status: "completed"
  },
  {
    id: "demo-2",
    model_name: "gpt-4o",
    provider: "openai", 
    dataset: "smoke",
    ttft_p50: 280,
    ttft_p95: 420,
    e2e_p50: 920,
    e2e_p95: 1400,
    avg_cost: 0.012,
    quality_score: 0.95,
    tokens_in: 850,
    tokens_out: 450,
    runs: 25,
    created_at: new Date().toISOString(),
    status: "completed"
  },
  {
    id: "demo-3",
    model_name: "deepseek-chat",
    provider: "deepseek",
    dataset: "smoke",
    ttft_p50: 150,
    ttft_p95: 280,
    e2e_p50: 550,
    e2e_p95: 850,
    avg_cost: 0.0008,
    quality_score: 0.88,
    tokens_in: 850,
    tokens_out: 410,
    runs: 25,
    created_at: new Date().toISOString(),
    status: "completed"
  }
];

async function getBenchmarks() {
  try {
    const benchmarks = await fetchApi<any[]>("/v1/benchmarks");
    return {
      benchmarks: benchmarks.length > 0 ? benchmarks : DEMO_BENCHMARKS,
      hasRealData: benchmarks.length > 0,
      error: null
    };
  } catch (error) {
    return {
      benchmarks: DEMO_BENCHMARKS,
      hasRealData: false,
      error: "API not available - showing demo benchmarks"
    };
  }
}

export default async function BenchmarksPage() {
  const { benchmarks, hasRealData, error } = await getBenchmarks();

  const formatValue = (value: number, type: 'time' | 'cost' | 'score') => {
    switch (type) {
      case 'time':
        return `${Math.round(value)}ms`;
      case 'cost':
        return `$${value.toFixed(4)}`;
      case 'score':
        return value.toFixed(2);
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.9) return "text-green-400";
    if (score >= 0.8) return "text-yellow-400";
    return "text-red-400";
  };

  const getCostColor = (cost: number) => {
    if (cost < 0.001) return "text-green-400";
    if (cost < 0.005) return "text-yellow-400";
    return "";
  };

  const getModelLabel = (provider: string, model: string) => {
    const providerColors: Record<string, string> = {
      openai: "border-green-400/30 bg-green-400/10",
      qwen: "border-blue-400/30 bg-blue-400/10",
      deepseek: "border-purple-400/30 bg-purple-400/10",
      anthropic: "border-orange-400/30 bg-orange-400/10"
    };
    return providerColors[provider] || "border-gray-400/30 bg-gray-400/10";
  };

  return (
    <div>
      <PageHeader title="Model Benchmarks">
        {hasRealData && (
          <div className="text-sm text-green-400">🟢 Live Data</div>
        )}
        <Link href="/benchmarks/new" className="btn">+ New Benchmark</Link>
      </PageHeader>

      {error && (
        <div className="mb-4 rounded-md border border-yellow-600/50 bg-yellow-600/10 p-3 text-sm text-yellow-300">
          {error}
        </div>
      )}

      {!hasRealData && (
        <div className="mb-4 rounded-lg border border-blue-600/30 bg-blue-600/10 p-4 text-sm">
          <h3 className="font-medium text-blue-300 mb-2">Run Your First Benchmark</h3>
          <p className="text-gray-300 mb-3">
            Compare different LLM models to find the optimal balance of speed, cost, and quality:
          </p>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <code className="block p-2 bg-black/30 rounded text-green-300 mb-1">
                agent-ops benchmark run --preset domestic
              </code>
              <span className="text-gray-400">Compare: qwen, deepseek, glm</span>
            </div>
            <div>
              <code className="block p-2 bg-black/30 rounded text-green-300 mb-1">
                agent-ops benchmark run --preset cost_efficient
              </code>
              <span className="text-gray-400">Compare: gpt-4o-mini, qwen-turbo</span>
            </div>
            <div>
              <code className="block p-2 bg-black/30 rounded text-green-300 mb-1">
                agent-ops benchmark run --models openai:gpt-4o
              </code>
              <span className="text-gray-400">Compare custom models</span>
            </div>
          </div>
        </div>
      )}

      <div className="card mb-4">
        <div className="flex justify-between items-center mb-2">
          <p className="text-[var(--muted)]">
            {hasRealData ? "Model comparison results:" : "Sample benchmark results:"}
          </p>
          {hasRealData && (
            <button className="text-sm text-indigo-400 hover:text-indigo-300">
              🔄 Refresh
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4 mb-6">
        <div className="col-span-3 card">
          <div className="text-xs text-gray-400 mb-1">TTFT</div>
          <div className="text-sm">Time to First Token</div>
        </div>
        <div className="col-span-3 card">
          <div className="text-xs text-gray-400 mb-1">E2E</div>
          <div className="text-sm">End-to-End Latency</div>
        </div>
        <div className="col-span-3 card">
          <div className="text-xs text-gray-400 mb-1">Cost</div>
          <div className="text-sm">Average Cost per Request</div>
        </div>
        <div className="col-span-3 card">
          <div className="text-xs text-gray-400 mb-1">Quality</div>
          <div className="text-sm">Task Success Score</div>
        </div>
      </div>

      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="border-b border-[var(--border)] bg-black/20">
            <tr>
              <th className="px-4 py-3 text-left">Model</th>
              <th className="px-4 py-3 text-right">TTFT</th>
              <th className="px-4 py-3 text-right">E2E</th>
              <th className="px-4 py-3 text-right">Cost</th>
              <th className="px-4 py-3 text-right">Quality</th>
              <th className="px-4 py-3 text-right">Runs</th>
              <th className="px-4 py-3 text-left">Last Run</th>
              <th className="px-4 py-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {benchmarks.map((benchmark) => (
              <tr key={benchmark.id} className="table-row">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs border ${getModelLabel(benchmark.provider, benchmark.model_name)}`}>
                      {benchmark.provider}
                    </span>
                    <span className="font-medium text-indigo-300">{benchmark.model_name}</span>
                  </div>
                  {hasRealData && (
                    <div className="text-xs text-gray-500 mt-1">
                      {benchmark.dataset} dataset
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="text-green-400">{formatValue(benchmark.ttft_p50, 'time')}</div>
                  <div className="text-xs text-gray-500">P50</div>
                </td>
                <td className="px-4 py-3 text-right">
                  <div>{formatValue(benchmark.e2e_p50, 'time')}</div>
                  <div className="text-xs text-gray-500">{formatValue(benchmark.e2e_p95, 'time')}</div>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className={getCostColor(benchmark.avg_cost)}>{formatValue(benchmark.avg_cost, 'cost')}</div>
                  <div className="text-xs text-gray-500">per run</div>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className={getQualityColor(benchmark.quality_score)}>
                    {formatValue(benchmark.quality_score, 'score')}
                  </div>
                  <div className="text-xs text-gray-500">score</div>
                </td>
                <td className="px-4 py-3 text-right">
                  <div>{benchmark.runs}</div>
                  <div className="text-xs text-gray-500">
                    {benchmark.tokens_in + benchmark.tokens_out} tokens
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">
                  {hasRealData ? (
                    <div>{new Date(benchmark.created_at).toLocaleDateString()}</div>
                  ) : (
                    "Demo data"
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-block w-2 h-2 rounded-full ${
                    benchmark.status === "completed" ? "bg-green-400" : 
                    benchmark.status === "running" ? "bg-yellow-400 animate-pulse" : "bg-red-400"
                  }`}></span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {!hasRealData && (
          <div className="px-4 py-3 text-xs text-[var(--muted)] border-t border-[var(--border)]">
            Click "+ New Benchmark" above to run your first real comparison
          </div>
        )}
      </div>
    </div>
  );
}
