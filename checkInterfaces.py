import os
import usb.core
import serial

class checker:

    def checkIP(self, ip_address):#pings ip address, VAR(Variables): IP address 
    print('checking ip address')
    response = os.system("ping -c 1 " + ip_address)
    #and then check the response...
    if response == 0:
        print(ip_address + ' was available')
    else:
        print(ip_address + ' was not available')
    time.sleep(1)

    def checkUSB(self, vid,pid):#pings usb device, input is theVID & PID of device
        print('checking USB Connection')
        dev = usb.core.find(idVendor= vid, idProduct= pid)
        if dev is None:
            print('USB device is NOT connected')
            print(vid + ' '+pid)
            print(" Device Crashed")
        else:
            print('USB device is connected') 
        time.sleep(1)

    def checkSerial(self, port_name,baud_rate,serial_parity='serial.PARITY_NONE',stop_bits=8,byte_size=8,time_out=1, command):
        #checks the serial interface, input is the port name, baud rate, parity, stopB, byteS, Timeout and the command depending on your device
        logger.debug('checking Serial Connection')
        ser = serial.Serial(
            port=port_name,
            baudrate=baud_rate,
            parity=serial_parity,
            stopbits=stop_bits,
            bytesize=byte_size,
            timeout=time_out
            )
        time.sleep(1)
        A=0
        try:
            ser.write(command.encode())
            for x in range(0,1000):
                if ser.inWaiting() > 10:
                    A=1
        finally:
            ser.close()
            if A==0:
                print(" Device Crashed")
            time.sleep(1)