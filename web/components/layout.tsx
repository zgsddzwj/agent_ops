"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/traces", label: "Traces" },
  { href: "/evals", label: "Evals" },
  { href: "/metrics", label: "Metrics" },
  { href: "/benchmarks", label: "Benchmarks" },
  { href: "/security", label: "Security" },
  { href: "/alerts", label: "Alerts" },
  { href: "/projects", label: "Projects" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed left-0 top-0 flex h-screen w-56 flex-col border-r border-[var(--border)] bg-[var(--card)] p-4">
      <div className="mb-8 text-lg font-bold text-indigo-400">AgentOps</div>
      <nav className="flex flex-col gap-1">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "rounded-md px-3 py-2 text-sm",
              pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
                ? "bg-indigo-600/20 text-indigo-300"
                : "text-[var(--muted)] hover:bg-white/5 hover:text-white"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
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

export function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="card">
      <div className="text-sm text-[var(--muted)]">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
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
