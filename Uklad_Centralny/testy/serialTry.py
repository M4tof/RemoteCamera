import serial
import time

# Open the serial port (ensure it's correct, usually /dev/ttyS0 for Raspberry Pi 3 or newer)
ser = serial.Serial('/dev/ttyAMA0', 9600)  # 9600 baud rate
time.sleep(2)  # wait for the serial connection to establish

# Send a message to Arduino
while True:
    message = "Hello from Raspberry Pi!"
    ser.write(message.encode())

    print(f"Sent: {message}")
    time.sleep(2)


ser.close()
