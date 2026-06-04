"use client";

import { PageHeader } from "@/components/layout";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const DEMO_DATA = [
  { bucket: "Mon", cost: 0.12, latency: 450 },
  { bucket: "Tue", cost: 0.18, latency: 520 },
  { bucket: "Wed", cost: 0.15, latency: 380 },
  { bucket: "Thu", cost: 0.22, latency: 610 },
  { bucket: "Fri", cost: 0.19, latency: 490 },
];

export default function MetricsPage() {
  return (
    <div>
      <PageHeader title="Metrics" />
      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <h2 className="mb-4 font-semibold">Cost Trend (USD)</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={DEMO_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="bucket" stroke="#71717a" />
              <YAxis stroke="#71717a" />
              <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a" }} />
              <Line type="monotone" dataKey="cost" stroke="#6366f1" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">P95 Latency (ms)</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={DEMO_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="bucket" stroke="#71717a" />
              <YAxis stroke="#71717a" />
              <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a" }} />
              <Line type="monotone" dataKey="latency" stroke="#22c55e" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
