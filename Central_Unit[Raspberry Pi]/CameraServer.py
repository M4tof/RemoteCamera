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

sharpness = 1
isoValue = 1.0
whiteBalanceRed = 1.0
whiteBalanceBlue = 1.0

currVar = 0
espInput = ""

servoBase = 100
servoUpper = 70

maxLight = 1400
minLight = 700

ledLights = [255,127,0]
lightValue = 20
lightRead = 1000
ledState = 3

lcdState = 5

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
        # Correct indentation here
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
            <li>Sharpness: <span id="sharpness"></span> µs</li>
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
                        document.getElementById('sharpness').textContent = data.sharpness;
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

def find_esp32_device(target_name="Wireless Controller ESP32"):
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True)
    for addr, name in nearby_devices:
        if target_name in name:
            return addr
    return None


def receive_messages(client_sock):
    global espInput,controllerAlive
    try:
        inputData = client_sock.recv(1024).decode("utf-8").strip()
        controllerAlive = 1000
        if inputData.strip():  
            espInput = inputData
            print("BTserial: " + str(espInput))
        return True
    except bluetooth.BluetoothError as e:
        return False

def send_messages(client_sock):
    global currVar
    flag = True
    while flag:
        try:
            client_sock.send(str(currVar)+"\n")
            flag = False
        except bluetooth.BluetoothError as e:
            flag = True

def input_processing():
    #Serial read from esp32
    global lightRead, espInput, currVar, lightValue, sharpness, isoValue, whiteBalanceRed, whiteBalanceBlue, servoBase, servoUpper,ledState, lcdState
    parsing = False
    number_str = ""
    if espInput:
        for char in espInput:
            if parsing and char.isdigit():
                    number_str += char
            if char == 'U':
                currVar += 1
                print("State: " + str(currVar))
                currVar %= 8
                break
            elif char == 'D':
                currVar -= 1
                currVar %= 8
                break
            elif char == 'S':
                parsing = True
                continue
            elif char == 'L' or char == 'R':
                match currVar:
                    case 0:
                        if char == 'L' and servoBase > 0:
                            servoBase -= 2
                        elif char == 'R' and servoBase < 180:
                            servoBase += 2
                    case 1:
                        if char == 'L' and servoUpper > 20:
                            servoUpper -= 2
                        elif char == 'R' and servoUpper < 160:
                            servoUpper += 2
                    case 2:
                        if char == 'L':
                            ledState -= 1
                        elif char == 'R':
                            ledState += 1
                        ledState = ledState%4
                    case 3:
                        if char == 'L':
                            lcdState -= 1
                        if char == 'R':
                            lcdState += 1
                        lcdState %= 5
                    case 4:
                        if char == 'L' and whiteBalanceRed > 0:
                            whiteBalanceRed -= 1
                        if char == 'R' and whiteBalanceRed < 10:
                            whiteBalanceRed += 1
                    case 5:
                        if char == 'L' and whiteBalanceBlue > 0:
                            whiteBalanceBlue -= 1
                        if char == 'R' and whiteBalanceBlue < 10:
                            whiteBalanceBlue += 1
                    case 6:
                        if char == 'L' and sharpness >= 0:
                            sharpness -= 1
                        if char == 'R' and sharpness < 17:
                            sharpness += 1
                    case _:
                        if char == 'L' and isoValue > 0:
                            isoValue -= 1
                        if char == 'R' and isoValue < 8:
                            isoValue += 1
                            
        if number_str:
            lightRead = int(number_str)
        if lightRead > maxLight:
            lightRead = maxLight
        if lightRead < minLight:
            lightRead = minLight
        lightRead -= minLight
        if ledState == 3: 
            lightValue = int(255 - lightRead*255/minLight)
        else:
            lightValue = ledLights[ledState]
        # print("LED set to react to => " + str(lightRead) + " light value.")
        # print("LED power set to => " + str(lightValue))


def bluetooth_control(): 
    global stop_threads, controllerAlive

    connected = False
    esp32_address = None

    while esp32_address is None:
        esp32_address = find_esp32_device(target_name="Wireless Controller ESP32")
        print("Controller found !")

    client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    
    def reconnect():
        nonlocal client_sock, esp32_address, connected
        while not stop_threads:
            try:
                client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                client_sock.connect((esp32_address, 1))
                connected = True
                print("Connected to ESP32.")
                return
            except bluetooth.BluetoothError as e:
                print(f"Reconnect failed: {e}. Retrying...")

    try:
        client_sock.connect((esp32_address, 1))
        connected = True
    except bluetooth.BluetoothError as e:
        reconnect()

    while not stop_threads:
        try:
            if not connected or controllerAlive <= 0:
                reconnect()

            if not receive_messages(client_sock):
                connected = False
                reconnect()
            else:
                input_processing()
                send_messages(client_sock)

        except bluetooth.BluetoothError as e:
            connected = False
            reconnect()

        controllerAlive -= 1
    client_sock.close()

def lcdControler():
    global lcdState, servoBase, lightRead, whiteBalanceBlue, whiteBalanceRed, isoValue, sharpness,stop_threads, executiveAlive,controllerAlive
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
                text = f"White Balance Blue: {whiteBalanceBlue}, White Balance Red: {whiteBalanceRed}, Iso: {isoValue}, Sharpness: {sharpness} "
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

@app.route('/view_settings')
def view_settings():
    return jsonify({
        "sharpness": sharpness,
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

        executiveAlive -= 1

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
    
    uart_thread = threading.Thread(target=executiveUnitControll, daemon=True)
    uart_thread.start()

    bluetooth_thread = threading.Thread(target=bluetooth_control, daemon=True)
    bluetooth_thread.start()

    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        cleanup()