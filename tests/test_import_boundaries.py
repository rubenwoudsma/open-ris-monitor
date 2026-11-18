"""Protect model isolation and diagnostics' ability to run before a harvest."""

from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"


def _run_python(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(SRC))
    result = subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, env=env, timeout=30
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_models_have_one_package_and_reexport_the_existing_types() -> None:
    assert not (SRC / "open_ris_monitor" / "models.py").exists()
    _run_python(
        "-c",
        textwrap.dedent("""
            from open_ris_monitor import models
            from open_ris_monitor.models.document import Document
            from open_ris_monitor.models.relations import Meeting, MeetingItem

            assert models.Document is Document
            assert models.Meeting is Meeting
            assert models.MeetingItem is MeetingItem
        """),
    )


def test_model_sources_only_depend_on_other_model_modules() -> None:
    for path in (SRC / "open_ris_monitor" / "models").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert node.level <= 1, f"Model import escapes its package: {path}"
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                if module.startswith("open_ris_monitor."):
                    assert module == "open_ris_monitor.models" or module.startswith(
                        "open_ris_monitor.models."
                    ), f"Model depends on application code: {path}: {module}"


@pytest.mark.parametrize(
    ("allowed", "imports"),
    [
        (
            ("models",),
            """
            from open_ris_monitor import models
            import open_ris_monitor.models.document_version
            import open_ris_monitor.models.harvest_run
            import open_ris_monitor.models.organization
            import open_ris_monitor.models.reports
            """,
        ),
        (
            ("connectors", "core", "diagnostics"),
            """
            import open_ris_monitor.diagnostics.gemeenteoplossingen_preflight
            import open_ris_monitor.diagnostics.gemeenteoplossingen_probe
            """,
        ),
    ],
    ids=["models-do-not-import-application-code", "diagnostics-do-not-import-pipeline"],
)
def test_imports_respect_layer_boundaries(allowed: tuple[str, ...], imports: str) -> None:
    guard = textwrap.dedent(f"""
        import importlib
        import importlib.abc
        import sys

        allowed = tuple('open_ris_monitor.' + name for name in {allowed!r})

        class BoundaryGuard(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.startswith('open_ris_monitor.') and not any(
                    fullname == prefix or fullname.startswith(prefix + '.') for prefix in allowed
                ):
                    raise AssertionError('Unexpected application dependency: ' + fullname)

        sys.meta_path.insert(0, BoundaryGuard())
    """)
    _run_python("-c", guard + textwrap.dedent(imports))


@pytest.mark.parametrize(
    "module",
    [
        "diagnostics.gemeenteoplossingen_preflight",
        "diagnostics.gemeenteoplossingen_probe",
        "pipeline.run",
        "analysis.generate_public_reports",
        "exporters.generate_schemas",
        "ci.publish_summary",
    ],
)
def test_workflow_entry_points_start_without_network_access(module: str) -> None:
    _run_python("-m", f"open_ris_monitor.{module}", "--help")
