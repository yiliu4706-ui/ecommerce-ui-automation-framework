"""
Network Condition Emulator

Uses Chrome DevTools Protocol to simulate various network conditions
for resilience testing.
"""

import logging
from typing import Dict, Any, Optional


class NetworkCondition:
    """Preset network condition profiles."""

    WIFI = {
        "offline": False,
        "latency": 20,
        "downloadThroughput": 30 * 1024 * 1024 / 8,
        "uploadThroughput": 15 * 1024 * 1024 / 8,
    }

    FOUR_G = {
        "offline": False,
        "latency": 100,
        "downloadThroughput": 4 * 1024 * 1024 / 8,
        "uploadThroughput": 3 * 1024 * 1024 / 8,
    }

    THREE_G = {
        "offline": False,
        "latency": 300,
        "downloadThroughput": 1600 * 1024 / 8,
        "uploadThroughput": 750 * 1024 / 8,
    }

    SLOW_3G = {
        "offline": False,
        "latency": 2000,
        "downloadThroughput": 400 * 1024 / 8,
        "uploadThroughput": 400 * 1024 / 8,
    }

    LOSSY = {
        "offline": False,
        "latency": 400,
        "downloadThroughput": 1 * 1024 * 1024 / 8,
        "uploadThroughput": 512 * 1024 / 8,
    }

    OFFLINE = {
        "offline": True,
        "latency": 0,
        "downloadThroughput": 0,
        "uploadThroughput": 0,
    }


class NetworkEmulator:
    """Wrapper for CDP network condition emulation."""

    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self._enabled = False

    def enable(self) -> None:
        if not self._enabled:
            self.driver.execute_cdp_cmd("Network.enable", {})
            self._enabled = True

    def apply(self, condition: Dict[str, Any]) -> None:
        self.enable()
        self.driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": condition.get("offline", False),
            "latency": condition.get("latency", 0),
            "downloadThroughput": condition.get("downloadThroughput", -1),
            "uploadThroughput": condition.get("uploadThroughput", -1),
        })
        self.logger.info(f"Network condition applied: {condition}")

    def reset(self) -> None:
        self.apply(NetworkCondition.WIFI)

    def clear_emulation(self) -> None:
        if self._enabled:
            try:
                self.driver.execute_cdp_cmd("Network.disable", {})
                self._enabled = False
            except Exception as e:
                self.logger.warning(f"Failed to disable network emulation: {e}")

    def apply_profile(self, profile_name: str) -> None:
        profiles = {
            "wifi": NetworkCondition.WIFI,
            "4g": NetworkCondition.FOUR_G,
            "3g": NetworkCondition.THREE_G,
            "slow_3g": NetworkCondition.SLOW_3G,
            "lossy": NetworkCondition.LOSSY,
            "offline": NetworkCondition.OFFLINE,
        }
        profile = profiles.get(profile_name.lower())
        if not profile:
            raise ValueError(f"Unknown network profile: {profile_name}")
        self.apply(profile)