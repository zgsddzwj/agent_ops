import os
from pathlib import Path

import httpx
import typer
import yaml
from rich.console import Console
from rich.table import Table

from agent_ops_cli.project_loader import (
    DEFAULT_MANIFEST,
    DEFAULT_SECURITY_POLICY,
    DEFAULT_SMOKE_EVAL,
    ProjectManifest,
)

console = Console()
app = typer.Typer(name="agent-ops", help="AgentOps CLI - evaluate and monitor AI agents")
init_app = typer.Typer(help="Initialize projects")
eval_app = typer.Typer(help="Run evaluations")
security_app = typer.Typer(help="Security scanning")
benchmark_app = typer.Typer(help="Model benchmarks")

app.add_typer(init_app, name="init")
app.add_typer(eval_app, name="eval")
app.add_typer(security_app, name="security")
app.add_typer(benchmark_app, name="benchmark")


def get_api_url() -> str:
    return os.environ.get("AGENT_OPS_API_URL", "http://localhost:8000")


@init_app.callback(invoke_without_command=True)
def init_project(
    project_path: Path = typer.Argument(..., help="Path to ai_project"),
):
    """Generate .agent-ops.yaml and example eval directories."""
    project_path = project_path.resolve()
    if not project_path.is_dir():
        typer.echo(f"Error: {project_path} is not a directory", err=True)
        raise typer.Exit(1)

    config_path = project_path / ".agent-ops.yaml"
    if config_path.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {config_path}")
    else:
        config_path.write_text(DEFAULT_MANIFEST.format(name=project_path.name))
        console.print(f"[green]Created[/green] {config_path}")

    evals_dir = project_path / "evals"
    evals_dir.mkdir(exist_ok=True)
    smoke_path = evals_dir / "smoke.yaml"
    if not smoke_path.exists():
        smoke_path.write_text(DEFAULT_SMOKE_EVAL)
        console.print(f"[green]Created[/green] {smoke_path}")

    sec_dir = project_path / "security"
    sec_dir.mkdir(exist_ok=True)
    policy_path = sec_dir / "policies.yaml"
    if not policy_path.exists():
        policy_path.write_text(DEFAULT_SECURITY_POLICY)
        console.print(f"[green]Created[/green] {policy_path}")

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  agent-ops link {project_path}")
    console.print(f"  agent-ops eval run --project {project_path} --suite smoke")


@app.command("link")
def link_project(
    project_path: Path = typer.Argument(..., help="Path to ai_project"),
    api_url: str = typer.Option(None, envvar="AGENT_OPS_API_URL"),
):
    """Register project with AgentOps platform and get API key."""
    project_path = project_path.resolve()
    manifest = ProjectManifest.load(project_path)

    url = api_url or get_api_url()
    payload = {
        "name": manifest.project,
        "root_path": str(manifest.root_path),
        "entrypoint": manifest.entrypoint,
        "config_yaml": manifest.config_yaml(),
    }

    try:
        resp = httpx.post(f"{url}/v1/projects", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        console.print(f"[red]Failed to register project:[/red] {e}")
        raise typer.Exit(1)

    api_key = data["api_key"]
    env_path = project_path / ".env.agent-ops"
    env_path.write_text(f"AGENT_OPS_API_KEY={api_key}\nAGENT_OPS_API_URL={url}\n")

    console.print(f"[green]Project registered:[/green] {data['name']} (id={data['id']})")
    console.print(f"[bold]API Key:[/bold] {api_key}")
    console.print(f"[dim]Saved to {env_path}[/dim]")


@eval_app.command("run")
def eval_run(
    project: Path = typer.Option(..., "--project", "-p"),
    suite: str = typer.Option("smoke", "--suite", "-s"),
    dataset: Path | None = typer.Option(None, "--dataset", "-d"),
    baseline: str | None = typer.Option(None, "--baseline"),
    api_url: str = typer.Option(None, envvar="AGENT_OPS_API_URL"),
    api_key: str = typer.Option(None, envvar="AGENT_OPS_API_KEY"),
):
    """Run evaluation suite against a project."""
    from agent_ops_cli.commands.eval import run_eval

    exit_code = run_eval(
        project_path=project.resolve(),
        suite=suite,
        dataset_path=dataset,
        baseline=baseline,
        api_url=api_url or get_api_url(),
        api_key=api_key,
    )
    raise typer.Exit(exit_code)


@security_app.command("scan")
def security_scan(
    project: Path = typer.Option(..., "--project", "-p"),
    suite: str = typer.Option("prompt_injection", "--suite", "-s"),
    api_url: str = typer.Option(None, envvar="AGENT_OPS_API_URL"),
    api_key: str = typer.Option(None, envvar="AGENT_OPS_API_KEY"),
):
    """Run security scan against a project."""
    from agent_ops_cli.commands.security import run_security_scan

    exit_code = run_security_scan(
        project_path=project.resolve(),
        suite=suite,
        api_url=api_url or get_api_url(),
        api_key=api_key,
    )
    raise typer.Exit(exit_code)


@benchmark_app.command("run")
def benchmark_run(
    project: Path = typer.Option(..., "--project", "-p"),
    models: str | None = typer.Option(None, "--models", "-m"),
    preset: str | None = typer.Option(None, "--preset"),
    dataset: Path | None = typer.Option(None, "--dataset", "-d"),
    repeat: int = typer.Option(3, "--repeat", "-r"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    api_url: str = typer.Option(None, envvar="AGENT_OPS_API_URL"),
    api_key: str = typer.Option(None, envvar="AGENT_OPS_API_KEY"),
):
    """Run multi-model benchmark comparison."""
    from agent_ops_cli.commands.benchmark import run_benchmark

    exit_code = run_benchmark(
        project_path=project.resolve(),
        models_str=models,
        preset=preset,
        dataset_path=dataset,
        repeat=repeat,
        output_path=output,
        api_url=api_url or get_api_url(),
        api_key=api_key,
    )
    raise typer.Exit(exit_code)


@app.command("check")
def check_project(
    project: Path = typer.Argument(...),
    suite: str = typer.Option("smoke", "--suite", "-s"),
    api_url: str = typer.Option(None, envvar="AGENT_OPS_API_URL"),
    api_key: str = typer.Option(None, envvar="AGENT_OPS_API_KEY"),
):
    """Run smoke eval + security scan (CI-friendly)."""
    from agent_ops_cli.commands.eval import run_eval
    from agent_ops_cli.commands.security import run_security_scan

    url = api_url or get_api_url()
    key = api_key or os.environ.get("AGENT_OPS_API_KEY")

    eval_code = run_eval(project.resolve(), suite=suite, api_url=url, api_key=key)
    sec_code = run_security_scan(project.resolve(), suite="prompt_injection", api_url=url, api_key=key)

    if eval_code != 0 or sec_code != 0:
        console.print("[red]Check failed[/red]")
        raise typer.Exit(1)
    console.print("[green]All checks passed[/green]")


if __name__ == "__main__":
    app()
