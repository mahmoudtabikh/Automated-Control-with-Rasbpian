"""Legacy import path. New code should import from cable_control."""

from cable_control import cables

# Example pinouts kept from the original module.
cable_1 = [2, 3, 4, 17]
cable_2 = [19, 26, 20, 21]


class cable_control:
    """Legacy class wrapper around the cable_control.cables functions."""

    def turnOn(self, cable):
        cables.turn_on(cable)

    def turnOff(self, offcable=None):
        cables.turn_off(offcable)

    def switchTime(self, sleep, cables_, testing_time):
        cables.switch_time(sleep, cables_, testing_time)

    def switchRandom(self, cables_, max_limit, testing_time):
        cables.switch_random(cables_, max_limit, testing_time)
