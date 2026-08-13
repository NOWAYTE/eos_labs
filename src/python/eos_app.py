#!/usr/bin/env python3
"""The single supported runtime entry point for EOS."""

from __future__ import annotations

import argparse
import asyncio
import json

from runtime_config import RuntimeProfile, load_profile


def assert_runnable(profile: RuntimeProfile) -> None:
    """Stop unsafe modes before any gateway or broker connection is opened."""
    if profile.mode == "research":
        return
    raise RuntimeError(
        f"Profile {profile.name!r} is not runnable yet: EOS has no account-state "
        "observer, RiskEngine, DecisionEngine, or execution adapter. Use the "
        "research profile for observation and replay only."
    )


async def run(profile: RuntimeProfile) -> None:
    assert_runnable(profile)
    from gateway import main as gateway_main

    await gateway_main(
        host=profile.gateway_host,
        port=profile.gateway_port,
        economic_config=profile.economic_config,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="EOS application launcher")
    parser.add_argument("--profile", default="research", help="Runtime profile from config/eos_profiles.json")
    parser.add_argument("--check", action="store_true", help="Validate and print the selected profile without starting")
    arguments = parser.parse_args()
    profile = load_profile(arguments.profile)
    if arguments.check:
        print(json.dumps({
            "name": profile.name,
            "mode": profile.mode,
            "gateway": f"{profile.gateway_host}:{profile.gateway_port}",
            "economic_config": str(profile.economic_config),
            "execution_enabled": profile.execution_enabled,
            "account_state_required": profile.account_state_required,
            "runnable": profile.mode == "research",
        }, indent=2, sort_keys=True))
        return
    asyncio.run(run(profile))


if __name__ == "__main__":
    main()
