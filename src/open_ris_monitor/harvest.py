"""Compatibility entry point for ``python -m open_ris_monitor.harvest``."""

from __future__ import annotations

from open_ris_monitor.pipeline.run import main


if __name__ == "__main__":
    main()
