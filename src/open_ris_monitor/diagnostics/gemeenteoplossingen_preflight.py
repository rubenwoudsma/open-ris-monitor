"""Cheap preflight checks for the configured GemeenteOplossingen API."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from open_ris_monitor.connectors.gemeenteoplossingen import (
    GemeenteOplossingenPreflightError,
    sanitize_url,
)
from open_ris_monitor.pipeline.run import build_connector, load_municipality_config


def _markdown_table(report: dict[str, Any]) -> str:
    lines = [
        "## Open RIS Monitor API preflight",
        "",
        f"Municipality: `{report['municipality']}`  ",
        f"Base URL: `{report['base_url']}`  ",
        f"Checked at: `{report['checked_at']}`",
        "",
        "| Endpoint | Status | Category | HTTP | Content-Type | Duration |",
        "| --- | --- | --- | ---: | --- | ---: |",
    ]
    for result in report["results"]:
        lines.append(
            "| `{endpoint}` | {status} | `{category}` | {http} | `{content_type}` | {duration} ms |".format(
                endpoint=result.get("endpoint", ""),
                status=result.get("status", "unknown"),
                category=result.get("category", "unknown"),
                http=result.get("status_code") or "",
                content_type=result.get("content_type") or "",
                duration=result.get("duration_ms") or 0,
            )
        )
    if report.get("failure_category"):
        lines.extend(
            [
                "",
                f"Failure category: `{report['failure_category']}`",
                "",
                "Recommended next step: verify upstream routing, WAF policy and public API access. "
                "Do not publish partial or empty data.",
            ]
        )
    return "\n".join(lines) + "\n"


def run_preflight(municipality: str) -> tuple[dict[str, Any], bool]:
    config = load_municipality_config(municipality)
    connector = build_connector(config)
    report: dict[str, Any] = {
        "municipality": municipality,
        "source_system_id": config["source_system"].get("id"),
        "base_url": sanitize_url(connector.base_url),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "results": [],
        "status": "failed",
        "failure_category": None,
    }
    try:
        report["results"] = connector.preflight()
    except GemeenteOplossingenPreflightError as exc:
        report["results"] = exc.results
        failure_categories = sorted(
            {
                str(result.get("category", "unknown"))
                for result in exc.results
                if result.get("status") != "ok"
            }
        )
        report["failure_category"] = ",".join(failure_categories) or exc.category
        return report, False
    report["status"] = "ok"
    return report, True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight the configured RIS API.")
    parser.add_argument("--municipality", default="huizen")
    parser.add_argument("--output", type=Path, default=Path("data/diagnostics/preflight.json"))
    parser.add_argument("--summary", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report, succeeded = run_preflight(args.municipality)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    markdown = _markdown_table(report)
    summary_path = args.summary
    if summary_path is None and os.environ.get("GITHUB_STEP_SUMMARY"):
        summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("a", encoding="utf-8") as summary_file:
            summary_file.write(markdown)

    for result in report["results"]:
        print(
            "preflight endpoint={endpoint} status={status} category={category} "
            "http={http} content_type={content_type} duration_ms={duration}".format(
                endpoint=result.get("endpoint"),
                status=result.get("status"),
                category=result.get("category"),
                http=result.get("status_code") or "",
                content_type=result.get("content_type") or "",
                duration=result.get("duration_ms") or 0,
            )
        )
        if result.get("body_preview"):
            print(f"preflight body_preview={result['body_preview']!r}")
    if not succeeded:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
