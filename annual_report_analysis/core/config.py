from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    output_dir: Path = Path("./annual_report_analysis/output")
    memory_store_dir: Path = Path("./annual_report_analysis/memory_store")
    max_chunk_chars: int = 3000
    force_agno: bool = False


DEFAULT_CONFIG = AppConfig()
