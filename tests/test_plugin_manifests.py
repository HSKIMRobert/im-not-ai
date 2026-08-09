"""Plugin manifests expose the current skill without duplicating references."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_plugin_versions_stay_in_sync() -> None:
    copilot = _load(ROOT / "plugin.json")
    claude = _load(ROOT / ".claude-plugin" / "plugin.json")
    marketplace = _load(ROOT / ".claude-plugin" / "marketplace.json")

    assert copilot["version"] == claude["version"]
    assert marketplace["metadata"]["version"] == copilot["version"]
    assert marketplace["plugins"][0]["version"] == copilot["version"]


def test_copilot_plugin_exposes_single_call_skill_and_references() -> None:
    manifest = _load(ROOT / "plugin.json")
    skill_root = (ROOT / manifest["skills"][0]).resolve()
    skill = skill_root / "humanize-korean"

    assert manifest["name"] == "humanize-korean"
    assert (skill / "SKILL.md").is_file()
    assert (skill / "references" / "quick-rules.md").is_file()
    assert (skill / "references" / "ai-tell-taxonomy.md").is_file()
    assert (skill / "references" / "rewriting-playbook.md").is_file()
