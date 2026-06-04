import tempfile
from pathlib import Path

import yaml


def test_load_manifest():
    from agent_ops_cli.project_loader import ProjectManifest, load_dataset

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = {
            "project": "test-bot",
            "entrypoint": "app.agent:graph",
            "invoke": {"method": "invoke", "input_key": "messages"},
        }
        (root / ".agent-ops.yaml").write_text(yaml.dump(config))
        (root / "evals").mkdir()
        (root / "evals" / "smoke.yaml").write_text(yaml.dump({
            "name": "smoke",
            "items": [{"input": "hi", "expected_behavior": "respond"}],
        }))

        manifest = ProjectManifest.load(root)
        assert manifest.project == "test-bot"
        assert manifest.entrypoint == "app.agent:graph"

        items = load_dataset(root / "evals" / "smoke.yaml")
        assert len(items) == 1
