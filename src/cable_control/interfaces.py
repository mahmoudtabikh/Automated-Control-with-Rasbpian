"""Check whether network, USB and serial devices respond."""

from __future__ import annotations

import ipaddress
import logging
import subprocess
import time

import serial
import usb.core

logger = logging.getLogger(__name__)

MAX_USB_ID = 0xFFFF
SERIAL_SETTLE_SECONDS = 1.0
SERIAL_POLL_SECONDS = 0.01
MIN_REPLY_BYTES = 10


def _validate_usb_id(value: object, name: str) -> int:
    """Return a USB vendor or product ID as an integer."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise TypeError(f"{name} must be an int or a hex string")
    if isinstance(value, str):
        try:
            value = int(value, 16)
        except ValueError:
            raise ValueError(f"{name} is not a valid hex string: {value!r}") from None
    if not 0 <= value <= MAX_USB_ID:
        raise ValueError(f"{name} must be between 0x0000 and 0xFFFF, got {value:#x}")
    return value


def check_ip(ip_address: str) -> bool:
    """Send one ping to an IPv4 or IPv6 address and return True on a reply."""
    if not isinstance(ip_address, str):
        raise TypeError("ip_address must be a string")
    address = str(ipaddress.ip_address(ip_address.strip()))
    logger.debug("pinging %s", address)
    result = subprocess.run(
        ["ping", "-c", "1", address],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    reachable = result.returncode == 0
    if reachable:
        logger.info("%s is reachable", address)
    else:
        logger.warning("%s is not reachable", address)
    return reachable


def check_usb(vid: int | str, pid: int | str) -> bool:
    """Return True if a USB device with the given vendor and product ID exists.

    IDs can be integers (0x1234) or hex strings ("1234" or "0x1234").
    """
    vendor = _validate_usb_id(vid, "vid")
    product = _validate_usb_id(pid, "pid")
    logger.debug("looking for USB device %04x:%04x", vendor, product)
    device = usb.core.find(idVendor=vendor, idProduct=product)
    if device is None:
        logger.warning("USB device %04x:%04x is not connected", vendor, product)
        return False
    logger.info("USB device %04x:%04x is connected", vendor, product)
    return True


def check_serial(
    port_name: str,
    baud_rate: int,
    serial_parity: str = serial.PARITY_NONE,
    stop_bits: float = serial.STOPBITS_ONE,
    byte_size: int = serial.EIGHTBITS,
    time_out: float = 1,
    command: str = "",
) -> bool:
    """Send a command to a serial device and return True if it answers.

    The device counts as answering when more than 10 bytes arrive within
    time_out seconds after the command was sent.

    Args:
        port_name: Serial port, for example "/dev/ttyUSB0".
        baud_rate: Baud rate, greater than zero.
        serial_parity: One of the pyserial PARITY constants.
        stop_bits: One of the pyserial STOPBITS constants.
        byte_size: One of the pyserial byte size constants.
        time_out: Time to wait for an answer in seconds, greater than zero.
        command: Text to send. Required. It must make the device reply.
    """
    if not isinstance(port_name, str) or not port_name:
        raise ValueError("port_name must be a non-empty string")
    if isinstance(baud_rate, bool) or not isinstance(baud_rate, int):
        raise TypeError("baud_rate must be an integer")
    if baud_rate <= 0:
        raise ValueError(f"baud_rate must be greater than zero, got {baud_rate}")
    if isinstance(time_out, bool) or not isinstance(time_out, (int, float)):
        raise TypeError("time_out must be a number")
    if time_out <= 0:
        raise ValueError(f"time_out must be greater than zero, got {time_out}")
    if not isinstance(command, str) or not command:
        raise ValueError("command must be a non-empty string")

    logger.debug("checking serial port %s", port_name)
    try:
        port = serial.Serial(
            port=port_name,
            baudrate=baud_rate,
            parity=serial_parity,
            stopbits=stop_bits,
            bytesize=byte_size,
            timeout=time_out,
        )
    except serial.SerialException as exc:
        logger.warning("could not open serial port %s: %s", port_name, exc)
        return False

    try:
        time.sleep(SERIAL_SETTLE_SECONDS)
        port.write(command.encode())
        deadline = time.monotonic() + time_out
        while time.monotonic() < deadline:
            if port.in_waiting > MIN_REPLY_BYTES:
                logger.info("serial device on %s answered", port_name)
                return True
            time.sleep(SERIAL_POLL_SECONDS)
    except serial.SerialException as exc:
        logger.warning("serial error on %s: %s", port_name, exc)
        return False
    finally:
        port.close()
    logger.warning("serial device on %s did not answer", port_name)
    return False


# Names used before the package layout existed.
checkIP = check_ip  # noqa: N816
checkUSB = check_usb  # noqa: N816
checkSerial = check_serial  # noqa: N816
