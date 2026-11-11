"""The import paths and class names from before the package layout."""

import serial

import cableControl
import checkInterfaces
from cable_control import interfaces


def test_legacy_cable_control_class(gpio, clock):
    control = cableControl.cable_control()
    control.turnOn(cableControl.cable_1)
    assert gpio.levels == dict.fromkeys(cableControl.cable_1, gpio.LOW)

    control.turnOff()
    assert gpio.levels == dict.fromkeys(cableControl.cable_1, gpio.HIGH)


def test_legacy_switch_methods(gpio, clock, monkeypatch):
    control = cableControl.cable_control()
    control.switchTime(20, [cableControl.cable_1], 1)
    assert clock.now == 60

    monkeypatch.setattr("cable_control.cables.random.randint", lambda low, high: 20)
    control.switchRandom([cableControl.cable_2], 30, 1)
    assert clock.now == 120


def test_legacy_checker_class(monkeypatch, clock):
    check = checkInterfaces.checker()

    monkeypatch.setattr(
        interfaces.subprocess,
        "run",
        lambda command, **kwargs: interfaces.subprocess.CompletedProcess(command, 0),
    )
    assert check.checkIP("10.0.0.1") is True

    monkeypatch.setattr(interfaces.usb.core, "find", lambda **kwargs: None)
    assert check.checkUSB(1, 2) is False

    def fail(**kwargs):
        raise serial.SerialException("no such port")

    monkeypatch.setattr(interfaces.serial, "Serial", fail)
    assert check.checkSerial("/dev/missing", 9600, command="x") is False
