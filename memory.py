from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state import AgentMessage, SectionName


class ShortTermMemory:
    def __init__(self, capacity: int = 20) -> None:
        self.capacity = capacity
        self.messages: List[AgentMessage] = []

    def add(self, message: AgentMessage) -> None:
        self.messages.append(message)
        if len(self.messages) > self.capacity:
            self.messages = self.messages[-self.capacity :]

    def get(self) -> List[AgentMessage]:
        return list(self.messages)


class LongTermMemory:
    def __init__(self, base_dir: str | Path = "./annual_report_analysis/memory_store") -> None:
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, agent_name: str, section: Optional[SectionName]) -> Path:
        section_part = section.value if section else "global"
        agent_dir = self.base_path / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir / f"{section_part}.jsonl"

    def upsert(self, agent_name: str, section: Optional[SectionName], key: str, value: Dict[str, Any]) -> None:
        path = self._path(agent_name, section)
        with path.open("a") as fp:
            fp.write(json.dumps({"key": key, "value": value}) + "\n")

    def query_all(self, agent_name: str, section: Optional[SectionName]) -> List[Dict[str, Any]]:
        path = self._path(agent_name, section)
        if not path.exists():
            return []
        results: List[Dict[str, Any]] = []
        with path.open() as fp:
            for line in fp:
                try:
                    results.append(json.loads(line))
                except Exception:
                    continue
        return results


