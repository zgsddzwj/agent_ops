"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Overview", icon: "📊" },
  { href: "/traces", label: "Traces", icon: "🔍" },
  { href: "/evals", label: "Evals", icon: "✅" },
  { href: "/metrics", label: "Metrics", icon: "📈" },
  { href: "/benchmarks", label: "Benchmarks", icon: "🤖" },
  { href: "/security", label: "Security", icon: "🛡️" },
  { href: "/alerts", label: "Alerts", icon: "🚨" },
  { href: "/projects", label: "Projects", icon: "📁" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed left-0 top-0 flex h-screen w-56 flex-col border-r border-[var(--border)] bg-[var(--card)] p-4">
      <div className="mb-8 flex items-center gap-2 text-lg font-bold text-indigo-400">
        <span className="text-xl">⚡</span>
        <span>AgentOps</span>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
              pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
                ? "bg-indigo-600/20 text-indigo-300"
                : "text-[var(--muted)] hover:bg-white/5 hover:text-white"
            )}
          >
            <span className="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="mt-auto pt-4 border-t border-[var(--border)]">
        <div className="text-xs text-[var(--muted)]">
          AgentOps v0.1.0
        </div>
      </div>
    </aside>
  );
}

export function ProjectSwitcher({ projects }: { projects: { id: string; name: string }[] }) {
  return (
    <select className="input" defaultValue="">
      <option value="">All Projects</option>
      {projects.map((p) => (
        <option key={p.id} value={p.id}>
          {p.name}
        </option>
      ))}
    </select>
  );
}

export function StatCard({
  label,
  value,
  sub,
  valueClassName,
}: {
  label: string;
  value: string;
  sub?: string;
  valueClassName?: string;
}) {
  return (
    <div className="card">
      <div className="text-sm text-[var(--muted)]">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${valueClassName || ""}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-[var(--muted)]">{sub}</div>}
    </div>
  );
}

export function PageHeader({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex items-center justify-between">
      <h1 className="text-2xl font-bold">{title}</h1>
      {children}
    </div>
  );
}
