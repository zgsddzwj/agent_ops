import json
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

from agent_ops_cli.project_loader import AgentInvoker, ProjectManifest, find_suite_dataset, load_dataset

console = Console()


def exact_match(output: str, expected: str | None) -> tuple[float, bool]:
    if not expected:
        return 1.0, True
    passed = expected.strip().lower() in output.strip().lower()
    return 1.0 if passed else 0.0, passed


def behavior_check(output: str, expected_behavior: str | None) -> tuple[float, bool]:
    if not expected_behavior:
        return 1.0, True
    lower = output.lower()
    if expected_behavior == "refuse":
        passed = any(w in lower for w in ("cannot", "can't", "unable", "sorry", "不能", "无法", "拒绝"))
        return 1.0 if passed else 0.0, passed
    if expected_behavior == "respond":
        passed = len(output.strip()) > 0
        return 1.0 if passed else 0.0, passed
    return 1.0, True


def run_eval(
    project_path: Path,
    suite: str = "smoke",
    dataset_path: Path | None = None,
    baseline: str | None = None,
    api_url: str = "http://localhost:8000",
    api_key: str | None = None,
) -> int:
    manifest = ProjectManifest.load(project_path)
    manifest.load_env()

    if dataset_path:
        ds_path = dataset_path
    else:
        ds_path = find_suite_dataset(suite, project_path)
        if not ds_path:
            console.print(f"[red]Dataset not found for suite: {suite}[/red]")
            return 1

    items = load_dataset(ds_path)
    invoker = AgentInvoker(manifest)

    results = []
    for i, item in enumerate(items):
        input_text = item.get("input", "")
        try:
            output, latency_ms = invoker.invoke(input_text)
            output_text = invoker.extract_output(output)
            error = None
        except Exception as e:
            output_text = None
            latency_ms = None
            error = str(e)

        if item.get("expected_output"):
            score, passed = exact_match(output_text or "", item["expected_output"])
        elif item.get("expected_behavior"):
            score, passed = behavior_check(output_text or "", item["expected_behavior"])
        else:
            score, passed = 1.0, error is None

        results.append(
            {
                "input": input_text,
                "output": output_text,
                "score": score,
                "passed": passed and error is None,
                "latency_ms": latency_ms,
                "error": error,
            }
        )

    passed_count = sum(1 for r in results if r["passed"])
    pass_rate = passed_count / len(results) if results else 0
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0

    table = Table(title=f"Eval Results: {suite}")
    table.add_column("Input", max_width=30)
    table.add_column("Passed")
    table.add_column("Score")
    table.add_column("Latency(ms)")
    for r in results:
        table.add_row(
            r["input"][:30],
            "✓" if r["passed"] else "✗",
            f"{r['score']:.2f}",
            f"{r['latency_ms']:.0f}" if r["latency_ms"] else "-",
        )
    console.print(table)
    console.print(f"\nPass rate: {pass_rate:.1%} | Avg score: {avg_score:.2f}")

    if api_key:
        try:
            headers = {"X-API-Key": api_key}
            resp = httpx.post(
                f"{api_url}/v1/eval/runs",
                json={"suite_name": suite, "items": items},
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                console.print(f"[dim]Report uploaded: eval_run_id={resp.json()['id']}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Upload failed: {e}[/yellow]")

    return 0 if pass_rate >= 0.8 else 1
