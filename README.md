# Automated-Control-with-Raspian


Files:
cableControl.py and checkInterfaces.py

This repo serves as a library for cable control using a raspberry pi and finding if extremeties are working/connected.

# do i need to install additional software ?

no, using a rpi is necessary for both libraries and cannot be ran using windows.
the following libraries would be imported:
import os
import usb.core
import serial
import time
import random
import logging
import RPi.GPIO as GPIO

# cableControl.py

- before starting you need to use the BCM cable connection to the RPI's GPIO pins and make a list of each one's pins.
- to turn on a cable you need to run the turnOn method with an input of the cable.
- to turn off a cable you need to use the turnOff method with an input of the cable.
- 2 useful functions are switchTime and switchRandom that:
    - switchTime switches between several selected cables with a user given time for a runtime T.
    - switchRandom switches between several selected cables with a random given time(user selects max time) for a runtime T.

# checkInterfaces.py

- before starting you need to know your USB device'S VID & PID hex nbs. and which protocol is used by your serial interface
- checkIP pings a given ip address and returns an answer.
- checkUSB checks if a USB device with a given VIP & PID is connected.
- checkSerial checks if a serial interface device is connected, all the settings are required as well as a command that requires an answer from the device.
