import serial
import time

# Open the serial port (ensure it's correct, usually /dev/ttyS0 for Raspberry Pi 3 or newer)
ser = serial.Serial('/dev/ttyAMA0', 9600)  # 9600 baud rate
time.sleep(2)  # wait for the serial connection to establish

# Send a message to Arduino
while True:
    if ser.in_waiting:  # Check if data is available to read
        data = ser.read(ser.in_waiting).decode('utf-8')  # Read and decode incoming data
        print(f"Received: {data}")

        lightValue = 90
        servoBase = 80
        servoUpper = 100

        commandLights = 'l'+str(lightValue)  # Add a newline for message delimitation if needed
        commandBase = 'b'+str(servoBase)
        commandUpper = 'u'+str(servoUpper)
        ser.write(commandLights.encode('utf-8'))  # Send the command as bytes
        ser.write(commandBase.encode('utf-8'))
        ser.write(commandUpper.encode('utf-8'))
            
        time.sleep(0.1)  # Add a small delay to prevent high CPU usage


ser.close()
