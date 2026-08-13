"""Single profile configuration boundary for EOS runtime modes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimeProfile:
    name: str
    mode: str
    gateway_host: str
    gateway_port: int
    economic_config: Path
    execution_enabled: bool
    account_state_required: bool
    live_execution_acknowledged: bool = False

    @property
    def is_research_only(self) -> bool:
        return self.mode == "research" and not self.execution_enabled


def load_profile(name: str, filename: str | Path | None = None) -> RuntimeProfile:
    if filename is None:
        filename = Path(__file__).parents[2] / "config" / "eos_profiles.json"
    filename = Path(filename)
    profiles = json.loads(filename.read_text(encoding="utf-8"))
    try:
        values = profiles[name]
    except KeyError as error:
        available = ", ".join(sorted(profiles))
        raise ValueError(f"Unknown EOS profile {name!r}; choose one of: {available}") from error
    values = dict(values)
    economic_config = filename.parent / values.pop("economic_config")
    profile = RuntimeProfile(name=name, economic_config=economic_config, **values)
    validate_profile(profile)
    return profile


def validate_profile(profile: RuntimeProfile) -> None:
    if profile.mode not in {"research", "paper", "live"}:
        raise ValueError(f"Invalid EOS mode: {profile.mode}")
    if not 1 <= profile.gateway_port <= 65535:
        raise ValueError("gateway_port must be between 1 and 65535")
    if not profile.economic_config.is_file():
        raise ValueError(f"Economic configuration not found: {profile.economic_config}")
    if profile.execution_enabled and profile.mode == "research":
        raise ValueError("Research profiles cannot enable execution")
