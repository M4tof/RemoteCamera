from picamera2 import Picamera2
from flask import Flask, Response, jsonify
from libcamera import Transform
import cv2
import threading
import time
import socket
import serial
import bluetooth
from LCD import LCD
import signal
import sys

stop_threads = False

exposureTimeMultiplier = 1
isoValue = 1.0
whiteBalanceRed = 1.0
whiteBalanceBlue = 1.0

aktualnaZmienna = 0

servoBase = 100
servoUpper = 70

ledLights = [255,127,0]
lightValue = 20
lightRead = 1000
ledState = 0

lcdState = 0

executiveAlive = 0
controllerAlive = 0

ser = serial.Serial('/dev/ttyAMA0', 9600)
lcd = LCD(2, 0x27, True) 
ipAddress = socket.gethostbyname(socket.gethostname())

app = Flask(__name__)

picam2 = Picamera2()
# Configure the camera for preview mode
camera_config = picam2.create_preview_configuration(
	transform=Transform(hflip=True, vflip=True), 
	buffer_count = 4)
picam2.configure(camera_config)
# Start the camera
picam2.start()


def generate_frames():
    while True:
        frame = picam2.capture_array()
        if frame is None:
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Correct indentation here
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return '''
        <h1>Raspberry Pi Camera Stream</h1>
        <img src="/video_feed" />
        <h2>Current Camera Settings:</h2>
        <ul id="settings">
            <li>Exposure Time: <span id="exposureTimeMultiplier"></span> µs</li>
            <li>ISO Value: <span id="isoValue"></span></li>
            <li>White Balance Red: <span id="whiteBalanceRed"></span></li>
            <li>White Balance Blue: <span id="whiteBalanceBlue"></span></li>
        </ul>
        <a href="/view_settings">View Settings in JSON</a>
        
        <script>
            // Function to fetch the latest settings from the server
            function fetchSettings() {
                fetch('/view_settings')
                    .then(response => response.json())
                    .then(data => {
                        // Update the HTML elements with the new values
                        document.getElementById('exposureTimeMultiplier').textContent = data.exposureTimeMultiplier;
                        document.getElementById('isoValue').textContent = data.isoValue;
                        document.getElementById('whiteBalanceRed').textContent = data.whiteBalanceRed;
                        document.getElementById('whiteBalanceBlue').textContent = data.whiteBalanceBlue;
                    })
                    .catch(error => console.error('Error fetching settings:', error));
            }

            // Set an interval to fetch new settings every 5 seconds
            setInterval(fetchSettings, 100); // Fetch every 5 seconds

            // Initial fetch to populate the settings on page load
            fetchSettings();
        </script>
    '''

def find_esp32_device(target_name="Wireless Controller ESP32"): #todo: zmienic nazwe
    """Function to scan for devices and find the ESP32."""
    print("Scanning for Bluetooth devices...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True)

    # Search for the ESP32 device by name
    for addr, name in nearby_devices:
        print(f"Found device: {name} ({addr})")
        if target_name in name:
            return addr  # Return the address if the ESP32 is found

    return None  # Return None if ESP32 is not found


# def receive_messages(client_sock):
#         try:
#             data = client_sock.recv(1024).decode("utf-8")
#             if not data:
#                 print("Connection closed by client.")
#             print(f"\nClient: {data}")
#         except bluetooth.BluetoothError as e:
#             print(f"Error receiving data: {e}")
#             break

# def send_messages(client_sock):
#     """Thread function to continuously send messages."""
#     while True:
#         try:
#             message = input("You: ")
#             if message.lower() == "exit":
#                 print("Ending chat.")
#                 client_sock.close()
#                 break
#             client_sock.send(message + "\n")
#         except bluetooth.BluetoothError as e:
#             print(f"Error sending data: {e}")
#             break

def bluetooth_control(): 
    global lcdState, servoBase, lightRead, whiteBalanceBlue, whiteBalanceRed, isoValue, exposureTimeMultiplier,stop_threads
    esp32_address = find_esp32_device(target_name="Wireless Controller ESP32")
    client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    while client_sock.connect((esp32_address, 1)) is None: #todo: sprawdz co zwraca funkcja (ale nie ma dokumentacji xD)
            esp32_address = find_esp32_device(target_name="Wireless Controller ESP32")
    while not stop_threads:
        receive_messages(client_sock)
        #send_messages(client_sock)
        #przetwarzanie()
        #receive_thread = threading.Thread(target=receive_messages, args=(client_sock,), daemon = True)
        #send_thread = threading.Thread(target=send_messages, args=(client_sock,), daemon = True)

    # Serial read from esp32
    # przetwórz wiadomość
#         #for char in wiadomość

#     #jeśli up down to zmień zmienną
#         #aktualnaZmienna += 1
#         #aktualnaZmienna -= 1
#         #aktualnaZmienna = aktualnaZmienna%8
      
#     #jeśli [S] to reszta wiadomości do zmapowania na 0-255 dla ledów 
#         #brake

#     global aktualnaZmienna, exposureTimeMultiplier, isoValue, whiteBalanceRed, whiteBalanceBlue
    

#     #if read == "L" or read == "R"
#         match aktualnaZmienna:
#             case 0:
#                 #if read = L &&  servoBase > 20 
#                     #then servoBase -= 1
#                     #send to arduino
#                         #message = "Hello from Raspberry Pi!"
#                         #ser.write(message.encode())
#                 #elif read = R && servoBase < 160
#                     #then servoBase += 1
#                     #send to Arduino
#             case 1: 
#                 #if read = L &&  servoUpper > 20 
#                     #then servoUpper -= 1
#                     #send to arduino
#                 #elif read = R && servoUpper < 160
#                     #then servoUpper += 1
#                     #send to Arduino
#             case 2:
#                 #if read == L
#                     #then ledState -= 1
#                 #elif read == R
#                     #then ledState += 1
#                 # ledState = ledState%4
#                 #match ledState
#                     #case 3:
#                         #arduino send zmapowane
#                     #case _:
#                         #arduino send ledLights[ledState]
#             case 3:
#                  #if read == L
#                     #then lcdState -= 1
#                 #elif read == R
#                     #then lcdState += 1
#                 #lcdState = lcdState%4
#             case 4:
#                 #if read == L && whiteBalanceRed > 0
#                     #then whiteBalanceRed -= 1
#                 #elif read == R && whiteBalanceRed < 10 
#                     #then whiteBalanceRed += 1
#             case 5:
#                 #if read == L && whiteBalanceBlue > 0
#                     #then whiteBalanceBlue -= 1
#                 #elif read == R && whiteBalanceBlue < 10 
#                     #then whiteBalanceBlue += 1
#             case 6: 
#                 #if read == L && exposureTimeMultiplier > 0
#                     #then exposureTimeMultiplier -= 1
#                 #elif read == R && exposureTimeMultiplier < 10 
#                     #then exposureTimeMultiplier += 1
#             case _:
#                 #if read == L && isoValue > 0
#                     #then isoValue -= 1
#                 #elif read == R && isoValue < 8 
#                     #then isoValue += 1

#         # picam2.set_controls({"AnalogueGain": iso_values[current_index]})
#         # picam2.set_controls({"ExposureTime": 1000000 * exposureTimeMultiplier })
#         # exposureTimeMultiplier += 1
#         # time.sleep(10)
#         # if exposureTimeMultiplier >= 8:
#         #     exposureTimeMultiplier = 1

def lcdControler():
    global lcdState, servoBase, lightRead, whiteBalanceBlue, whiteBalanceRed, isoValue, exposureTimeMultiplier,stop_threads, executiveAlive,controllerAlive
    Current = lcdState

    while not stop_threads:
        if Current != lcdState:
            lcd.clear()
            Current = lcdState
        match lcdState:
            case 0:
                lcd.message("Serwer na: ", 1)
                lcd.message(ipAddress + ":5000", 2)
            case 1:
                lcd.message("Oswietlenie: ",1)
                lcd.message(str(lightRead),2)
            case 2:
                lcd.message("Dolne serwo:" + str(servoBase) ,1)
                lcd.message("Gorne serwo:" + str(servoUpper),2)
            case 3:
                text = f"WB: {whiteBalanceBlue}, WR: {whiteBalanceRed}, Iso: {isoValue}, EXPT: {exposureTimeMultiplier} "
                full_text = text + text
                for i in range(len(text)):  # 16 is the number of characters that fit on the LCD screen
                    scroll_text = full_text[i:i+16]
                    lcd.message("Wartosci kamery:",1)  # Clear the second line
                    lcd.message(scroll_text,2)  # Display the current window of text
                    time.sleep(0.4)
                    if Current != lcdState or stop_threads:
                        break
            case _:
                if executiveAlive > 0:
                    lcd.message("Wykonawcze On",1)
                else:
                    lcd.message("Wykonawcze Off",1)
                if controllerAlive > 0:
                    lcd.message("Kontroler On",2)
                else:
                    lcd.message("Kontroler Off",2)

        # time.sleep(5/100)

def DebugChanger():
    global lcdState, servoBase, lightRead, whiteBalanceBlue, whiteBalanceRed, isoValue, exposureTimeMultiplier
    while True:
        time.sleep(5)
        lcdState -= 1
        lcdState = lcdState%5
        isoValue += 1

@app.route('/view_settings')
def view_settings():
    return jsonify({
        "exposureTimeMultiplier": exposureTimeMultiplier,
        "isoValue": isoValue,
        "whiteBalanceRed": whiteBalanceRed,
        "whiteBalanceBlue": whiteBalanceBlue
    })

def executiveUnitControll():
    global executiveAlive, servoBase, servoUpper, lightValue, stop_threads, ser
    last_command = {"lightValue": None, "servoBase": None, "servoUpper": None}

    while not stop_threads:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting).decode('utf-8')
            executiveAlive = 1000  # Reset heartbeat counter

        # Send commands only if values have changed
        if last_command["lightValue"] != lightValue:
            ser.write(f'l{lightValue}\n'.encode('utf-8'))
            last_command["lightValue"] = lightValue

        if last_command["servoBase"] != servoBase:
            ser.write(f'b{servoBase}\n'.encode('utf-8'))
            last_command["servoBase"] = servoBase

        if last_command["servoUpper"] != servoUpper:
            ser.write(f'u{servoUpper}\n'.encode('utf-8'))
            last_command["servoUpper"] = servoUpper

        time.sleep(0.1)  # Adjust delay to avoid flooding the UART


def cleanup():
    global stop_threads
    print("Cleaning up and shutting down...")
    
    stop_threads = True
    time.sleep(1)
    picam2.stop()
    ser.close()
    
    lcd.clear()
    lcd.backlight = False
    
    print("Cleanup complete. Exiting...")
    sys.exit(0)

if __name__ == '__main__':

    def signal_handler(sig, frame):
        cleanup()

    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # Handle termination signals

    lcd_thread = threading.Thread(target=lcdControler, daemon=True)
    lcd_thread.start()
    
    uart_thrad = threading.Thread(target=executiveUnitControll, daemon=True)
    uart_thrad.start()

    changer_thread = threading.Thread(target=DebugChanger, daemon=True)
    changer_thread.start()

    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        cleanup()