import { PageHeader, StatCard } from "@/components/layout";
import { fetchApi } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";

type MetricPoint = {
  bucket: string;
  cost: number;
  latency: number;
  runs: number;
};

// Fallback demo data when API is not available
const DEMO_DATA: MetricPoint[] = [
  { bucket: "Mon", cost: 0.12, latency: 450, runs: 15 },
  { bucket: "Tue", cost: 0.18, latency: 520, runs: 22 },
  { bucket: "Wed", cost: 0.15, latency: 380, runs: 18 },
  { bucket: "Thu", cost: 0.22, latency: 610, runs: 31 },
  { bucket: "Fri", cost: 0.19, latency: 490, runs: 25 },
];

async function getMetricsData() {
  try {
    const [metrics, timeseries] = await Promise.all([
      fetchApi<any>("/v1/metrics/summary").catch(() => null),
      fetchApi<any[]>("/v1/metrics/timeseries?days=7").catch(() => null),
    ]);
    
    // Transform timeseries data to match our chart format
    const chartData = timeseries?.map(point => ({
      bucket: new Date(point.bucket).toLocaleDateString('en-US', { weekday: 'short' }),
      cost: point.total_cost_usd || 0,
      latency: point.p95_latency_ms || 0,
      runs: point.run_count || 0,
    })) || DEMO_DATA;
    
    return {
      chartData,
      summary: metrics,
      hasRealData: !!timeseries,
      error: null
    };
  } catch (error) {
    return {
      chartData: DEMO_DATA,
      summary: null,
      hasRealData: false,
      error: "API not available - showing demo data"
    };
  }
}

export default async function MetricsPage() {
  const { chartData, summary, hasRealData, error } = await getMetricsData();
  
  const formatValue = (value: number, type: 'currency' | 'time' | 'count') => {
    switch (type) {
      case 'currency':
        return `$${value.toFixed(3)}`;
      case 'time':
        return `${Math.round(value)}ms`;
      case 'count':
        return value.toString();
    }
  };

  return (
    <div>
      <PageHeader title="Metrics & Analytics">
        {hasRealData && (
          <div className="text-sm text-green-400">🟢 Live Data</div>
        )}
      </PageHeader>
      
      {error && (
        <div className="mb-4 rounded-md border border-yellow-600/50 bg-yellow-600/10 p-3 text-sm text-yellow-300">
          {error}
        </div>
      )}
      
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard 
            label="Total Runs" 
            value={String(summary.total_runs)} 
            sub={`$${summary.total_cost_usd.toFixed(3)} cost`} 
          />
          <StatCard 
            label="Total Tokens" 
            value={formatValue(summary.total_tokens || 0, 'count')} 
            sub={`Avg: ${Math.round((summary.total_tokens || 0) / Math.max(summary.total_runs, 1))} per run`} 
          />
          <StatCard 
            label="Avg Latency" 
            value={formatValue(summary.avg_latency_ms || 0, 'time')} 
            sub={`P95: ${formatValue(summary.p95_latency_ms || 0, 'time')}`} 
          />
          <StatCard 
            label="Error Rate" 
            value={`${((summary.error_rate || 0) * 100).toFixed(1)}%`} 
            sub="Target: <5%" 
          />
        </div>
      )}
      
      {/* Charts */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <h2 className="mb-4 font-semibold">Cost Trend (USD)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="bucket" stroke="#71717a" />
              <YAxis stroke="#71717a" tickFormatter={(value) => formatValue(value, 'currency')} />
              <Tooltip 
                contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a" }}
                formatter={(value: number) => [formatValue(value, 'currency'), 'Cost']}
              />
              <Line type="monotone" dataKey="cost" stroke="#6366f1" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="card">
          <h2 className="mb-4 font-semibold">P95 Latency (ms)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="bucket" stroke="#71717a" />
              <YAxis stroke="#71717a" tickFormatter={(value) => formatValue(value, 'time')} />
              <Tooltip 
                contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a" }}
                formatter={(value: number) => [formatValue(value, 'time'), 'P95 Latency']}
              />
              <Line type="monotone" dataKey="latency" stroke="#22c55e" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="card col-span-2">
          <h2 className="mb-4 font-semibold">Daily Request Volume</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="bucket" stroke="#71717a" />
              <YAxis stroke="#71717a" />
              <Tooltip 
                contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a" }}
                formatter={(value: number) => [value.toString(), 'Runs']}
              />
              <Bar dataKey="runs" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {!hasRealData && (
        <div className="mt-4 p-4 rounded-lg border border-blue-600/30 bg-blue-600/10 text-sm">
          <h3 className="font-medium text-blue-300 mb-2">Get Real Metrics</h3>
          <p className="text-gray-300">
            Connect your AI agent with the AgentOps SDK to start collecting real performance data:
          </p>
          <code className="block mt-2 p-2 bg-black/30 rounded text-green-300 text-xs">
            from agent_ops import AgentOpsCallbackHandler<br/>
            handler = AgentOpsCallbackHandler(client)<br/>
            result = agent.invoke(input, config={'callbacks': [handler]})
          </code>
        </div>
      )}
    </div>
  );
}
