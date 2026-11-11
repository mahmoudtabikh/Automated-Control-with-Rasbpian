"""Legacy import path. New code should import from cable_control."""

from cable_control import interfaces


class checker:
    """Legacy class wrapper around the cable_control.interfaces functions."""

    def checkIP(self, ip_address):
        return interfaces.check_ip(ip_address)

    def checkUSB(self, vid, pid):
        return interfaces.check_usb(vid, pid)

    def checkSerial(self, port_name, baud_rate, *args, **kwargs):
        return interfaces.check_serial(port_name, baud_rate, *args, **kwargs)
