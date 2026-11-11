"""Shared fakes so the tests run without Raspberry Pi hardware."""

from __future__ import annotations

import sys
import types

import pytest

from cable_control import cables, interfaces


class FakeGPIO(types.ModuleType):
    """Stand-in for RPi.GPIO that records every call."""

    BCM = "BCM"
    OUT = "OUT"
    HIGH = 1
    LOW = 0

    def __init__(self) -> None:
        super().__init__("RPi.GPIO")
        self.calls: list[tuple] = []
        self.levels: dict[int, int] = {}

    def setmode(self, mode):
        self.calls.append(("setmode", mode))

    def setwarnings(self, flag):
        self.calls.append(("setwarnings", flag))

    def setup(self, pin, direction):
        self.calls.append(("setup", pin, direction))

    def output(self, pin, level):
        self.calls.append(("output", pin, level))
        self.levels[pin] = level

    def cleanup(self):
        self.calls.append(("cleanup",))


class FakeClock:
    """Clock whose sleep() advances time instantly."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def gpio(monkeypatch):
    """Install a fake RPi.GPIO module and reset the cables module state."""
    fake = FakeGPIO()
    package = types.ModuleType("RPi")
    package.GPIO = fake
    monkeypatch.setitem(sys.modules, "RPi", package)
    monkeypatch.setitem(sys.modules, "RPi.GPIO", fake)
    monkeypatch.setattr(cables, "_gpio", None)
    monkeypatch.setattr(cables, "_active_pins", set())
    return fake


@pytest.fixture
def clock(monkeypatch):
    """Replace the time module in both modules with a fake clock."""
    fake = FakeClock()
    monkeypatch.setattr(cables, "time", fake)
    monkeypatch.setattr(interfaces, "time", fake)
    return fake
