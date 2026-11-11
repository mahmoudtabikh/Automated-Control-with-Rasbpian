import subprocess

import pytest
import serial

import cable_control
from cable_control import interfaces


class FakeSerial:
    """Stand-in for serial.Serial with a scripted number of waiting bytes."""

    def __init__(self, waiting=0, fail_on_write=False, **kwargs):
        self.kwargs = kwargs
        self.in_waiting = waiting
        self.fail_on_write = fail_on_write
        self.written = b""
        self.closed = False

    def write(self, data):
        if self.fail_on_write:
            raise serial.SerialException("write failed")
        self.written += data

    def close(self):
        self.closed = True


@pytest.fixture
def ping(monkeypatch):
    """Replace subprocess.run and record the commands it receives."""
    state = {"returncode": 0, "commands": []}

    def fake_run(command, **kwargs):
        state["commands"].append(command)
        return subprocess.CompletedProcess(command, state["returncode"])

    monkeypatch.setattr(interfaces.subprocess, "run", fake_run)
    return state


@pytest.fixture
def serial_port(monkeypatch):
    """Make serial.Serial return a FakeSerial that tests can configure."""
    state = {"waiting": 0, "fail_on_write": False, "ports": []}

    def factory(**kwargs):
        port = FakeSerial(state["waiting"], state["fail_on_write"], **kwargs)
        state["ports"].append(port)
        return port

    monkeypatch.setattr(interfaces.serial, "Serial", factory)
    return state


def test_check_ip_reachable(ping):
    assert interfaces.check_ip("192.168.0.10") is True
    assert ping["commands"] == [["ping", "-c", "1", "192.168.0.10"]]


def test_check_ip_unreachable(ping):
    ping["returncode"] = 1
    assert interfaces.check_ip("192.168.0.10") is False


def test_check_ip_accepts_ipv6(ping):
    assert interfaces.check_ip("::1") is True


@pytest.mark.parametrize(
    "address", ["", "not an ip", "256.1.1.1", "8.8.8.8; rm -rf /", "example.com"]
)
def test_check_ip_rejects_invalid_address(ping, address):
    with pytest.raises(ValueError):
        interfaces.check_ip(address)
    assert ping["commands"] == []


def test_check_ip_rejects_non_string(ping):
    with pytest.raises(TypeError):
        interfaces.check_ip(3232235530)


def test_check_usb_connected(monkeypatch):
    seen = {}

    def fake_find(**kwargs):
        seen.update(kwargs)
        return object()

    monkeypatch.setattr(interfaces.usb.core, "find", fake_find)
    assert interfaces.check_usb(0x1234, 0xABCD) is True
    assert seen == {"idVendor": 0x1234, "idProduct": 0xABCD}


def test_check_usb_not_connected(monkeypatch):
    monkeypatch.setattr(interfaces.usb.core, "find", lambda **kwargs: None)
    assert interfaces.check_usb(0x1234, 0xABCD) is False


def test_check_usb_accepts_hex_strings(monkeypatch):
    seen = {}
    monkeypatch.setattr(interfaces.usb.core, "find", lambda **kw: seen.update(kw))
    interfaces.check_usb("0x1234", "abcd")
    assert seen == {"idVendor": 0x1234, "idProduct": 0xABCD}


@pytest.mark.parametrize(
    ("vid", "pid", "error"),
    [
        (-1, 1, ValueError),
        (1, 0x10000, ValueError),
        ("xyz", 1, ValueError),
        (1.5, 1, TypeError),
        (None, 1, TypeError),
        (True, 1, TypeError),
    ],
)
def test_check_usb_rejects_bad_ids(monkeypatch, vid, pid, error):
    def fail(**kwargs):
        raise AssertionError("usb.core.find must not be called")

    monkeypatch.setattr(interfaces.usb.core, "find", fail)
    with pytest.raises(error):
        interfaces.check_usb(vid, pid)


def test_check_serial_device_answers(serial_port, clock):
    serial_port["waiting"] = 11
    assert interfaces.check_serial("/dev/ttyUSB0", 9600, command="ID?\n") is True

    port = serial_port["ports"][0]
    assert port.written == b"ID?\n"
    assert port.closed
    assert port.kwargs == {
        "port": "/dev/ttyUSB0",
        "baudrate": 9600,
        "parity": serial.PARITY_NONE,
        "stopbits": serial.STOPBITS_ONE,
        "bytesize": serial.EIGHTBITS,
        "timeout": 1,
    }


def test_check_serial_accepts_positional_arguments(serial_port, clock):
    serial_port["waiting"] = 50
    result = interfaces.check_serial(
        "/dev/ttyUSB0", 115200, serial.PARITY_EVEN, 2, 7, 3, "ID?"
    )
    assert result is True
    assert serial_port["ports"][0].kwargs["parity"] == serial.PARITY_EVEN


def test_check_serial_times_out_when_reply_is_too_short(serial_port, clock):
    serial_port["waiting"] = 10
    assert (
        interfaces.check_serial("/dev/ttyUSB0", 9600, time_out=2, command="x") is False
    )

    # 1 s settle time after opening the port, then 2 s of polling.
    assert clock.now == pytest.approx(3, abs=0.02)
    assert serial_port["ports"][0].closed


def test_check_serial_port_cannot_be_opened(monkeypatch, clock):
    def fail(**kwargs):
        raise serial.SerialException("no such port")

    monkeypatch.setattr(interfaces.serial, "Serial", fail)
    assert interfaces.check_serial("/dev/missing", 9600, command="x") is False


def test_check_serial_write_error_closes_port(serial_port, clock):
    serial_port["fail_on_write"] = True
    assert interfaces.check_serial("/dev/ttyUSB0", 9600, command="x") is False
    assert serial_port["ports"][0].closed


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"port_name": "", "baud_rate": 9600, "command": "x"}, ValueError),
        ({"port_name": None, "baud_rate": 9600, "command": "x"}, ValueError),
        ({"port_name": "p", "baud_rate": 0, "command": "x"}, ValueError),
        ({"port_name": "p", "baud_rate": "9600", "command": "x"}, TypeError),
        (
            {"port_name": "p", "baud_rate": 9600, "time_out": 0, "command": "x"},
            ValueError,
        ),
        (
            {"port_name": "p", "baud_rate": 9600, "time_out": -1, "command": "x"},
            ValueError,
        ),
        (
            {"port_name": "p", "baud_rate": 9600, "time_out": "1", "command": "x"},
            TypeError,
        ),
        ({"port_name": "p", "baud_rate": 9600}, ValueError),
        ({"port_name": "p", "baud_rate": 9600, "command": b"x"}, ValueError),
    ],
)
def test_check_serial_rejects_bad_input(serial_port, clock, kwargs, error):
    with pytest.raises(error):
        interfaces.check_serial(**kwargs)
    assert serial_port["ports"] == []


def test_package_exports_old_and_new_names():
    assert cable_control.checkIP is cable_control.check_ip
    assert cable_control.checkUSB is cable_control.check_usb
    assert cable_control.checkSerial is cable_control.check_serial
