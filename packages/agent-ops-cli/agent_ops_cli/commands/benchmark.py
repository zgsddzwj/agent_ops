import json
from pathlib import Path

import httpx
import yaml
from rich.console import Console
from rich.table import Table

from agent_ops_cli.project_loader import (
    AgentInvoker,
    ModelCandidate,
    ProjectManifest,
    find_suite_dataset,
    load_dataset,
    parse_models_arg,
)

console = Console()

PRESETS: dict[str, list[ModelCandidate]] = {
    "domestic": [
        ModelCandidate("qwen", "qwen-plus"),
        ModelCandidate("qwen", "qwen-turbo"),
        ModelCandidate("deepseek", "deepseek-chat"),
        ModelCandidate("zhipu", "glm-4"),
    ],
    "international": [
        ModelCandidate("openai", "gpt-4o"),
        ModelCandidate("openai", "gpt-4o-mini"),
        ModelCandidate("anthropic", "claude-sonnet-4-20250514"),
    ],
    "sota": [
        ModelCandidate("openai", "gpt-4o"),
        ModelCandidate("anthropic", "claude-sonnet-4-20250514"),
        ModelCandidate("qwen", "qwen-max"),
        ModelCandidate("deepseek", "deepseek-reasoner"),
    ],
    "cost_efficient": [
        ModelCandidate("openai", "gpt-4o-mini"),
        ModelCandidate("qwen", "qwen-turbo"),
        ModelCandidate("deepseek", "deepseek-chat"),
    ],
}


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    idx = min(int(len(s) * p / 100), len(s) - 1)
    return s[idx]


def run_benchmark(
    project_path: Path,
    models_str: str | None = None,
    preset: str | None = None,
    dataset_path: Path | None = None,
    repeat: int = 3,
    output_path: Path | None = None,
    api_url: str = "http://localhost:8000",
    api_key: str | None = None,
) -> int:
    manifest = ProjectManifest.load(project_path)
    manifest.load_env()

    if models_str:
        models = parse_models_arg(models_str)
    elif preset:
        models = PRESETS.get(preset, [])
        if not models:
            console.print(f"[red]Unknown preset: {preset}[/red]")
            return 1
    else:
        models = manifest.model_candidates or PRESETS["cost_efficient"]

    if dataset_path:
        ds_path = dataset_path
    else:
        ds_path = find_suite_dataset("smoke", project_path)
        if not ds_path:
            console.print("[red]No dataset found[/red]")
            return 1

    items = load_dataset(ds_path)
    invoker = AgentInvoker(manifest)

    all_results: list[dict] = []

    for model in models:
        console.print(f"\n[bold]Testing {model.provider}:{model.model}[/bold]")
        if manifest.swap_hook:
            try:
                invoker.swap_model(model.provider, model.model)
            except Exception as e:
                console.print(f"[yellow]Swap hook failed: {e}[/yellow]")

        model_results = []
        for case_idx, item in enumerate(items):
            input_text = item.get("input", "")
            case_ttfts = []
            case_e2es = []
            case_costs = []
            last_output = None

            for rep in range(repeat):
                try:
                    result, e2e_ms = invoker.invoke(input_text)
                    output = invoker.extract_output(result)
                    last_output = output
                    case_e2es.append(e2e_ms)
                    # TTFT approximated as 30% of e2e without streaming hook
                    case_ttfts.append(e2e_ms * 0.3 if e2e_ms else None)
                except Exception as e:
                    model_results.append(
                        {
                            "provider": model.provider,
                            "model": model.model,
                            "case_index": case_idx,
                            "repeat_index": rep,
                            "error": str(e),
                        }
                    )
                    continue

                model_results.append(
                    {
                        "provider": model.provider,
                        "model": model.model,
                        "case_index": case_idx,
                        "repeat_index": rep,
                        "ttft_ms": case_ttfts[-1],
                        "e2e_latency_ms": e2e_ms,
                        "eval_score": 1.0 if output else 0.0,
                        "output_text": output,
                    }
                )

        all_results.extend(model_results)

    # Aggregate per model
    by_model: dict[str, list] = {}
    for r in all_results:
        key = f"{r['provider']}:{r['model']}"
        by_model.setdefault(key, []).append(r)

    table = Table(title="Model Benchmark Comparison")
    table.add_column("Model")
    table.add_column("TTFT P50")
    table.add_column("E2E P50")
    table.add_column("E2E P95")
    table.add_column("Errors")

    summary = {"models": []}
    for key, results in by_model.items():
        ttfts = [r["ttft_ms"] for r in results if r.get("ttft_ms")]
        e2es = [r["e2e_latency_ms"] for r in results if r.get("e2e_latency_ms")]
        errors = sum(1 for r in results if r.get("error"))
        entry = {
            "model": key,
            "ttft_p50": percentile(ttfts, 50),
            "ttft_p95": percentile(ttfts, 95),
            "e2e_p50": percentile(e2es, 50),
            "e2e_p95": percentile(e2es, 95),
            "error_rate": errors / len(results) if results else 0,
        }
        summary["models"].append(entry)
        table.add_row(
            key,
            f"{entry['ttft_p50']:.0f}ms" if entry["ttft_p50"] else "-",
            f"{entry['e2e_p50']:.0f}ms" if entry["e2e_p50"] else "-",
            f"{entry['e2e_p95']:.0f}ms" if entry["e2e_p95"] else "-",
            str(errors),
        )

    console.print(table)

    if output_path:
        output_path.write_text(json.dumps(summary, indent=2))
        console.print(f"[dim]Saved to {output_path}[/dim]")

    if api_key:
        try:
            headers = {"X-API-Key": api_key}
            models_payload = [{"provider": m.provider, "model": m.model} for m in models]
            resp = httpx.post(
                f"{api_url}/v1/benchmarks",
                json={"models": models_payload, "repeat_count": repeat, "items": items},
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                console.print(f"[dim]Benchmark uploaded: id={resp.json()['id']}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Upload failed: {e}[/yellow]")

    return 0
