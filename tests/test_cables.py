import sys

import pytest

import cable_control
from cable_control import cables

CABLE_A = [2, 3]
CABLE_B = [19, 26]


def test_turn_on_drives_pins_low_and_waits(gpio, clock):
    cables.turn_on(CABLE_A)

    assert ("setmode", gpio.BCM) in gpio.calls
    assert ("setup", 2, gpio.OUT) in gpio.calls
    assert gpio.levels == {2: gpio.LOW, 3: gpio.LOW}
    assert clock.sleeps == [cables.DEFAULT_SETTLE_SECONDS]


def test_turn_on_custom_settle_time(gpio, clock):
    cables.turn_on(CABLE_A, settle_time=0)
    assert clock.sleeps == [0.0]


def test_turn_off_drives_pins_high(gpio, clock):
    cables.turn_on(CABLE_A)
    cables.turn_off(CABLE_A)
    assert gpio.levels == {2: gpio.HIGH, 3: gpio.HIGH}


def test_turn_off_without_argument_turns_off_active_pins(gpio, clock):
    cables.turn_on(CABLE_A)
    cables.turn_on(CABLE_B)
    cables.turn_off()
    assert gpio.levels == dict.fromkeys(CABLE_A + CABLE_B, gpio.HIGH)
    assert cables._active_pins == set()


def test_turn_off_without_argument_and_nothing_active(gpio):
    cables.turn_off()
    assert not [call for call in gpio.calls if call[0] == "output"]


def test_gpio_mode_is_set_only_once(gpio, clock):
    cables.turn_on(CABLE_A)
    cables.turn_on(CABLE_B)
    assert gpio.calls.count(("setmode", gpio.BCM)) == 1


@pytest.mark.parametrize("cable", [[-1], [28], [2, 99]])
def test_pin_out_of_range_raises_value_error(gpio, cable):
    with pytest.raises(ValueError):
        cables.turn_on(cable)
    assert gpio.calls == []


@pytest.mark.parametrize("cable", [[2.0], ["2"], [True], "23", 2, None])
def test_wrong_cable_type_raises_type_error(gpio, cable):
    with pytest.raises(TypeError):
        cables.turn_on(cable)


def test_empty_cable_raises_value_error(gpio):
    with pytest.raises(ValueError):
        cables.turn_off([])


def test_negative_settle_time_raises(gpio):
    with pytest.raises(ValueError):
        cables.turn_on(CABLE_A, settle_time=-1)


def test_settle_time_must_be_a_number(gpio):
    with pytest.raises(TypeError):
        cables.turn_on(CABLE_A, settle_time="1")


def test_switch_time_cycles_until_deadline(gpio, clock):
    # One cycle takes 10 s settle + 20 s hold, so one pass over two cables
    # takes 60 s. A run time of 2 minutes gives exactly two passes.
    cables.switch_time(20, [CABLE_A, CABLE_B], 2)

    low_writes = [c for c in gpio.calls if c == ("output", 2, gpio.LOW)]
    assert len(low_writes) == 2
    assert clock.now == 120
    assert gpio.levels == dict.fromkeys(CABLE_A + CABLE_B, gpio.HIGH)


def test_switch_time_finishes_a_started_pass(gpio, clock):
    cables.switch_time(20, [CABLE_A, CABLE_B], 0.1)
    assert clock.now == 60


def test_switch_time_turns_cable_off_on_interrupt(gpio, clock, monkeypatch):
    def interrupted_sleep(seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(clock, "sleep", interrupted_sleep)
    with pytest.raises(KeyboardInterrupt):
        cables.switch_time(1, [CABLE_A], 1)
    assert gpio.levels == {2: gpio.HIGH, 3: gpio.HIGH}


@pytest.mark.parametrize(
    ("sleep", "cable_list", "minutes", "error"),
    [
        (-1, [CABLE_A], 1, ValueError),
        (1, [], 1, ValueError),
        (1, [CABLE_A], 0, ValueError),
        (1, [CABLE_A], -5, ValueError),
        (1, [[40]], 1, ValueError),
        ("1", [CABLE_A], 1, TypeError),
        (1, "cables", 1, TypeError),
        (1, [CABLE_A], None, TypeError),
    ],
)
def test_switch_time_rejects_bad_input(gpio, clock, sleep, cable_list, minutes, error):
    with pytest.raises(error):
        cables.switch_time(sleep, cable_list, minutes)
    assert gpio.calls == []


def test_switch_random_draws_one_hold_time_per_pass(gpio, clock, monkeypatch):
    draws = []

    def fake_randint(low, high):
        draws.append((low, high))
        return 5

    monkeypatch.setattr(cables.random, "randint", fake_randint)
    # One pass: 2 cables * (10 s settle + 5 s hold) = 30 s.
    cables.switch_random([CABLE_A, CABLE_B], 7, 1)

    assert draws == [(1, 7), (1, 7)]
    assert clock.now == 60
    assert clock.sleeps.count(5) == 4
    assert gpio.levels == dict.fromkeys(CABLE_A + CABLE_B, gpio.HIGH)


@pytest.mark.parametrize(
    ("max_limit", "error"),
    [(0, ValueError), (-3, ValueError), (1.5, TypeError), (True, TypeError)],
)
def test_switch_random_rejects_bad_max_limit(gpio, clock, max_limit, error):
    with pytest.raises(error):
        cables.switch_random([CABLE_A], max_limit, 1)


def test_cleanup_releases_gpio_and_resets_state(gpio, clock):
    cables.turn_on(CABLE_A)
    cables.cleanup()
    assert gpio.calls[-1] == ("cleanup",)
    assert cables._gpio is None
    assert cables._active_pins == set()


def test_cleanup_without_gpio_use_does_nothing(gpio):
    cables.cleanup()
    assert gpio.calls == []


def test_gpio_session_cleans_up_on_success(gpio, clock):
    with cables.gpio_session():
        cables.turn_on(CABLE_A)
    assert gpio.calls[-1] == ("cleanup",)


def test_gpio_session_cleans_up_on_error(gpio, clock):
    with pytest.raises(ValueError), cables.gpio_session():
        cables.turn_on([99])
    assert gpio.calls[-1] == ("cleanup",)


def test_missing_rpi_gpio_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(cables, "_gpio", None)
    monkeypatch.setitem(sys.modules, "RPi", None)
    monkeypatch.setitem(sys.modules, "RPi.GPIO", None)
    with pytest.raises(RuntimeError, match="RPi.GPIO is not installed"):
        cables.turn_on(CABLE_A)


def test_package_exports_old_and_new_names():
    assert cable_control.turnOn is cable_control.turn_on
    assert cable_control.turnOff is cable_control.turn_off
    assert cable_control.switchTime is cable_control.switch_time
    assert cable_control.switchRandom is cable_control.switch_random
