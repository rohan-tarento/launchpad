"""Tests for AGENTS.md run-section preservation during apply-harness."""

from __future__ import annotations

from launchpad.commands.apply_harness import _preserve_agents_run_section


def test_preserve_agents_run_section_keeps_existing_commands(tmp_path) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        """# Agent guide

## Run and verify

- Setup: [`README.md`](README.md)

```bash
make check
make test

make verify-smoke
```

Custom setup notes here.

---

## Before changing behavior

1. Read specs.
""",
        encoding="utf-8",
    )

    template = """# Agent guide

## Run and verify

- Setup and run: [`README.md`](README.md)

```bash
{{CHECK_COMMAND}}
{{TEST_COMMAND}}

{{VERIFY_SMOKE}}
```

{{SETUP_NOTES}}

---

## Before changing behavior

1. Template step.
"""

    result = _preserve_agents_run_section(template, agents)

    assert "make check" in result
    assert "make verify-smoke" in result
    assert "Custom setup notes here." in result
    assert "{{CHECK_COMMAND}}" not in result


def test_preserve_agents_run_section_no_existing_file(tmp_path) -> None:
    template = "## Run and verify\n\n```bash\n{{CHECK_COMMAND}}\n```\n\n---\n"
    result = _preserve_agents_run_section(template, tmp_path / "AGENTS.md")
    assert "{{CHECK_COMMAND}}" in result


def test_preserve_agents_run_section_skips_placeholder_existing(tmp_path) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "## Run and verify\n\n```bash\n{{CHECK_COMMAND}}\n```\n\n---\n",
        encoding="utf-8",
    )
    template = "## Run and verify\n\n```bash\nmake lint\n```\n\n---\n"
    result = _preserve_agents_run_section(template, agents)
    assert "make lint" in result
    assert "{{CHECK_COMMAND}}" not in result
