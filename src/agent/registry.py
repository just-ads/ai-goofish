"""Agent plugin registry.

This package is for *in-process agents* (plugins), not model providers.
A plugin is a concrete capability (e.g. product evaluation).
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Callable, Dict


AgentFactory = Callable[..., Any]


_AGENT_FACTORIES: Dict[str, AgentFactory] = {}
_PLUGINS_LOADED = False


def register_agent(agent_id: str, factory: AgentFactory) -> None:
    if not agent_id:
        raise ValueError("agent_id cannot be empty")

    if agent_id in _AGENT_FACTORIES:
        raise ValueError(f"duplicate agent_id: {agent_id}")

    _AGENT_FACTORIES[agent_id] = factory


def _load_plugins() -> None:
    global _PLUGINS_LOADED
    if _PLUGINS_LOADED:
        return

    # Import all modules under src.agent.plugins so they can self-register.
    import src.agent.plugins as plugins_pkg

    for module_info in pkgutil.iter_modules(plugins_pkg.__path__, plugins_pkg.__name__ + "."):
        importlib.import_module(module_info.name)

    _PLUGINS_LOADED = True


def create_agent(agent_id: str, **kwargs: Any) -> Any:
    _load_plugins()

    factory = _AGENT_FACTORIES.get(agent_id)
    if not factory:
        raise KeyError(f"unknown agent plugin: {agent_id}")

    return factory(**kwargs)
