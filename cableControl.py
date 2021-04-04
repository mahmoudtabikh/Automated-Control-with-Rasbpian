#libraries and warnings
import time
import random
import logging
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#logger Config, for log msg format: logRec attributes pyth
logger= logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('The cable control logger just started')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(funcName)s:%(message)s')
stream_handler=logging.StreamHandler()
logger.addHandler(stream_handler)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#GPIO PINS Pinout for cables, list with the cable name
cable_1 = [2, 3, 4, 17]
cable_2 = [19,26,20,21]

class cable_control:
    def turnOn(self, cable):
        #turns ON a cable, input is a list with the cable pins
        t1='turning ON Cable'
        logger.debug(t1)
        for i in cable:
            GPIO.setup(i, GPIO.OUT)
            GPIO.output(i, GPIO.HIGH)
            GPIO.output(i, GPIO.LOW)
        time.sleep(10)

    def turnOff(offcable=ALL):
        #turns off a cable, input is a list with the cable pins
        for i in offcable:
            GPIO.setup(i, GPIO.OUT)
            GPIO.output(i, GPIO.HIGH)

    def switchTime(self, sleep, cables, testing_time):
        #turns on several defined cables interchangeably, input is a list of the cables, switching time in seconds and run time in minutes
        logger.debug('starting the switching function')
        t_end= time.time() + testing_time*60
        while time.time() < t_end:
            for cable in cables:
                GPIO.setup(cable,GPIO.OUT)
                self.turnOn(cable)
                time.sleep(sleep)
                self.turnOff(cable)
        logger.debug('Intercable test finished')

    def switchRandom(self, cables,max_limit, testing_time):
        #turns on several defined cables interchangeably with random times, input is the cables, runtime in minutes and max time of switching in seconds
        logger.debug('Random test starting')
        t_end= time.time() + testing_time*60
        while time.time() < t_end:
            rand=random.randint(1,max_limit) #random pin
            for cable in cables:
                GPIO.setup(cable,GPIO.OUT)
                self.turnOn(cable)
                time.sleep(rand)
                self.turnOff(cable)
        logger.debug('Random test finished')

# NEVER FORGET TO GPIO.cleanup() AT THE END FOR AN Exit cleanout
