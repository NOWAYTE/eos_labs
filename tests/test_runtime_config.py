import unittest

from eos_app import assert_runnable
from runtime_config import load_profile


class RuntimeProfileTests(unittest.TestCase):
    def test_research_profile_is_runnable_and_execution_is_disabled(self):
        profile = load_profile("research")

        assert_runnable(profile)
        self.assertTrue(profile.is_research_only)
        self.assertFalse(profile.execution_enabled)

    def test_live_profile_is_refused_until_trading_prerequisites_exist(self):
        profile = load_profile("live")

        with self.assertRaisesRegex(RuntimeError, "account-state observer"):
            assert_runnable(profile)
