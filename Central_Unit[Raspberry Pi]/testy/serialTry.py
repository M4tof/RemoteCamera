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

            # Uncomment the following line if you want to send data
            # ser.write(b'Hello from Raspberry Pi\n')
            
        time.sleep(0.1)  # Add a small delay to prevent high CPU usage


ser.close()
