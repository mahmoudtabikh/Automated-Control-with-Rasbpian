"""Switch cables that are wired to Raspberry Pi GPIO pins.

A cable is a sequence of BCM pin numbers. The wiring is assumed to be
active-low: a pin driven LOW connects its line, a pin driven HIGH
disconnects it.
"""

from __future__ import annotations

import importlib
import logging
import random
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

MIN_BCM_PIN = 0
MAX_BCM_PIN = 27
DEFAULT_SETTLE_SECONDS = 10.0

Cable = Sequence[int]

_gpio: Any = None
_active_pins: set[int] = set()


def _get_gpio() -> Any:
    """Import RPi.GPIO on first use and select BCM pin numbering."""
    global _gpio
    if _gpio is None:
        try:
            gpio = importlib.import_module("RPi.GPIO")
        except ImportError as exc:
            raise RuntimeError(
                "RPi.GPIO is not installed. Install this package with the "
                "'pi' extra on a Raspberry Pi."
            ) from exc
        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)
        _gpio = gpio
    return _gpio


def _validate_number(value: object, name: str, *, allow_zero: bool) -> float:
    """Return value as a float after checking type and range."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if value < 0 or (value == 0 and not allow_zero):
        limit = "zero or greater" if allow_zero else "greater than zero"
        raise ValueError(f"{name} must be {limit}, got {value}")
    return float(value)


def _validate_cable(cable: object) -> list[int]:
    """Return the pins of a cable after checking each pin number."""
    if isinstance(cable, (str, bytes)) or not isinstance(cable, Sequence):
        raise TypeError("a cable must be a list or tuple of BCM pin numbers")
    if not cable:
        raise ValueError("a cable must contain at least one pin")
    for pin in cable:
        if isinstance(pin, bool) or not isinstance(pin, int):
            raise TypeError(f"pin numbers must be integers, got {pin!r}")
        if not MIN_BCM_PIN <= pin <= MAX_BCM_PIN:
            raise ValueError(
                f"pin {pin} is outside the BCM range {MIN_BCM_PIN} to {MAX_BCM_PIN}"
            )
    return list(cable)


def _validate_cables(cables: object) -> list[list[int]]:
    """Return a list of validated cables."""
    if isinstance(cables, (str, bytes)) or not isinstance(cables, Sequence):
        raise TypeError("cables must be a list or tuple of cables")
    if not cables:
        raise ValueError("cables must contain at least one cable")
    return [_validate_cable(cable) for cable in cables]


def turn_on(cable: Cable, settle_time: float = DEFAULT_SETTLE_SECONDS) -> None:
    """Connect a cable, then wait settle_time seconds."""
    pins = _validate_cable(cable)
    settle = _validate_number(settle_time, "settle_time", allow_zero=True)
    gpio = _get_gpio()
    logger.debug("turning on cable %s", pins)
    for pin in pins:
        gpio.setup(pin, gpio.OUT)
        gpio.output(pin, gpio.HIGH)
        gpio.output(pin, gpio.LOW)
        _active_pins.add(pin)
    time.sleep(settle)


def turn_off(cable: Cable | None = None) -> None:
    """Disconnect a cable. Without an argument, disconnect every active pin."""
    pins = sorted(_active_pins) if cable is None else _validate_cable(cable)
    gpio = _get_gpio()
    logger.debug("turning off cable %s", pins)
    for pin in pins:
        gpio.setup(pin, gpio.OUT)
        gpio.output(pin, gpio.HIGH)
        _active_pins.discard(pin)


def _cycle(cable: Cable, hold: float) -> None:
    """Connect a cable for hold seconds and always disconnect it afterwards."""
    try:
        turn_on(cable)
        time.sleep(hold)
    finally:
        turn_off(cable)


def switch_time(sleep: float, cables: Sequence[Cable], testing_time: float) -> None:
    """Cycle through cables, holding each for a fixed time.

    Args:
        sleep: Hold time per cable in seconds.
        cables: The cables to cycle through.
        testing_time: Total run time in minutes. A pass over all cables
            that has started is always finished.
    """
    hold = _validate_number(sleep, "sleep", allow_zero=True)
    checked = _validate_cables(cables)
    minutes = _validate_number(testing_time, "testing_time", allow_zero=False)
    logger.debug("starting fixed-time switching")
    deadline = time.monotonic() + minutes * 60
    while time.monotonic() < deadline:
        for cable in checked:
            _cycle(cable, hold)
    logger.debug("fixed-time switching finished")


def switch_random(cables: Sequence[Cable], max_limit: int, testing_time: float) -> None:
    """Cycle through cables with a random hold time.

    One hold time between 1 and max_limit seconds is drawn for each pass
    over all cables.

    Args:
        cables: The cables to cycle through.
        max_limit: Largest hold time in whole seconds, at least 1.
        testing_time: Total run time in minutes. A pass over all cables
            that has started is always finished.
    """
    checked = _validate_cables(cables)
    if isinstance(max_limit, bool) or not isinstance(max_limit, int):
        raise TypeError("max_limit must be an integer")
    if max_limit < 1:
        raise ValueError(f"max_limit must be at least 1, got {max_limit}")
    minutes = _validate_number(testing_time, "testing_time", allow_zero=False)
    logger.debug("starting random switching")
    deadline = time.monotonic() + minutes * 60
    while time.monotonic() < deadline:
        hold = random.randint(1, max_limit)
        for cable in checked:
            _cycle(cable, hold)
    logger.debug("random switching finished")


def cleanup() -> None:
    """Release all GPIO pins. Safe to call when GPIO was never used."""
    global _gpio
    if _gpio is None:
        return
    try:
        _gpio.cleanup()
    finally:
        _gpio = None
        _active_pins.clear()


@contextmanager
def gpio_session() -> Iterator[None]:
    """Context manager that releases all GPIO pins on exit."""
    _get_gpio()
    try:
        yield
    finally:
        cleanup()


# Names used before the package layout existed.
turnOn = turn_on  # noqa: N816
turnOff = turn_off  # noqa: N816
switchTime = switch_time  # noqa: N816
switchRandom = switch_random  # noqa: N816
