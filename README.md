# Automated Control with Raspbian

A small Python library for the Raspberry Pi that does two things:

- switches cables that are wired to GPIO pins, for example through a relay board
- checks whether a network host, a USB device or a serial device responds

It is meant for automated hardware tests, such as plugging and unplugging
a cable many times and checking after each step that the device is still
reachable.

## Requirements

- Raspberry Pi running Raspberry Pi OS (Raspbian) for real use
- Python 3.10 or newer
- `ping` on the system path for `check_ip`

The tests use fakes for all hardware, so they run on any machine.

## Installation

On the Raspberry Pi:

```bash
pip install "rpi-cable-control[pi] @ git+https://github.com/mahmoudtabikh/Automated-Control-with-Rasbpian"
```

The `pi` extra installs `RPi.GPIO`. Leave it out on other machines.
`pyserial` and `pyusb` are always installed.

For development:

```bash
git clone https://github.com/mahmoudtabikh/Automated-Control-with-Rasbpian
cd Automated-Control-with-Rasbpian
pip install -e ".[dev]"
```

## Cable control

A cable is a list of BCM pin numbers (0 to 27). Each pin switches one
line of the cable.

The wiring is assumed to be active-low: `turn_on` drives the pins LOW
and `turn_off` drives them HIGH.

```python
from cable_control import gpio_session, switch_random, switch_time, turn_off, turn_on

cable_1 = [2, 3, 4, 17]
cable_2 = [19, 26, 20, 21]

with gpio_session():
    turn_on(cable_1)
    turn_off(cable_1)

    # Hold each cable for 5 seconds, run for 10 minutes.
    switch_time(5, [cable_1, cable_2], 10)

    # Hold each cable for a random 1 to 30 seconds, run for 10 minutes.
    switch_random([cable_1, cable_2], 30, 10)
```

| Function | Description |
| --- | --- |
| `turn_on(cable, settle_time=10)` | Connects a cable, then waits `settle_time` seconds. |
| `turn_off(cable=None)` | Disconnects a cable. Without an argument it disconnects every pin that was turned on. |
| `switch_time(sleep, cables, testing_time)` | Connects the cables one after another. Each stays connected for `sleep` seconds. Runs for `testing_time` minutes. |
| `switch_random(cables, max_limit, testing_time)` | Same, but the hold time is a random whole number of seconds between 1 and `max_limit`, drawn once per pass over all cables. |
| `gpio_session()` | Context manager that calls `GPIO.cleanup()` on exit, also after an error. |
| `cleanup()` | Releases all GPIO pins. Use it if you do not use `gpio_session()`. |

Notes:

- The switching functions use `turn_on`, so every cycle also includes the
  10 second settle time.
- The run time is checked once per pass. A pass that has started is
  always finished.
- If a switching function is interrupted, the cable that is currently
  connected is disconnected first.

## Interface checks

Each check returns `True` or `False` and logs the result.

```python
from cable_control import check_ip, check_serial, check_usb

check_ip("192.168.0.10")
check_usb(0x1234, 0xABCD)
check_serial("/dev/ttyUSB0", 9600, command="ID?\n")
```

| Function | Description |
| --- | --- |
| `check_ip(ip_address)` | Sends one ping to an IPv4 or IPv6 address. |
| `check_usb(vid, pid)` | Looks for a USB device with the given vendor ID and product ID. IDs are integers or hex strings, from 0x0000 to 0xFFFF. |
| `check_serial(port_name, baud_rate, serial_parity, stop_bits, byte_size, time_out, command)` | Opens the port, sends `command` and returns `True` if more than 10 bytes arrive within `time_out` seconds. |

`check_serial` defaults to no parity, 1 stop bit, 8 data bits and a
1 second timeout. `command` is required and must be a command that makes
your device send a reply.

## Errors and logging

- Invalid arguments raise `ValueError` or `TypeError` before any hardware
  is touched.
- Using the cable functions without `RPi.GPIO` installed raises
  `RuntimeError`.
- A serial port that cannot be opened makes `check_serial` return `False`.

The library logs through the standard `logging` module under the logger
name `cable_control` and does not configure any handlers. To see the
messages:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## Old import paths

The original modules still work:

```python
from cableControl import cable_control
from checkInterfaces import checker

cable_control().turnOn([2, 3, 4, 17])
checker().checkIP("192.168.0.10")
```

The old camelCase names (`turnOn`, `turnOff`, `switchTime`, `switchRandom`,
`checkIP`, `checkUSB`, `checkSerial`) are also available from
`cable_control`. New code should use the snake_case names.

## Development

```bash
ruff check .
ruff format --check .
pytest
```

`pytest` prints a coverage report. `RPi.GPIO`, `usb.core`, `serial`, `ping`
and the clock are replaced with fakes in the tests. GitHub Actions runs the
same commands on Python 3.10, 3.11 and 3.12.
