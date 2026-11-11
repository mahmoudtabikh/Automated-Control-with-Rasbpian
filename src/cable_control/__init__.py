"""Cable switching and interface checks for the Raspberry Pi."""

import logging

from cable_control.cables import (
    cleanup,
    gpio_session,
    switch_random,
    switch_time,
    switchRandom,
    switchTime,
    turn_off,
    turn_on,
    turnOff,
    turnOn,
)
from cable_control.interfaces import (
    check_ip,
    check_serial,
    check_usb,
    checkIP,
    checkSerial,
    checkUSB,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"

__all__ = [
    "checkIP",
    "checkSerial",
    "checkUSB",
    "check_ip",
    "check_serial",
    "check_usb",
    "cleanup",
    "gpio_session",
    "switchRandom",
    "switchTime",
    "switch_random",
    "switch_time",
    "turnOff",
    "turnOn",
    "turn_off",
    "turn_on",
]
