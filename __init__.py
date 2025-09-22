"""Self-contained annual report analysis workflow (no external dependencies).

Modules:
- state: data types and section enums
- memory: short-/long-term memory (local JSONL)
- tools: loader, chunker, heuristics, sentiment/risk stubs
- prompts: static guidance strings (optional)
- agents: supervisor and section agents (rule-based)
- workflow: orchestrator loop
- runner: CLI entrypoint
- cli: argparse-based CLI entrypoint
- agno_support: Agno team wiring and runtime
- config: app configuration dataclass
"""

__all__ = [
    "state",
    "memory",
    "tools",
    "prompts",
    "agents",
    "workflow",
    "runner",
    "cli",
    "agno_support",
    "config",
]


