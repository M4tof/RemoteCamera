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
analogueGain = 3
whiteBalanceRed = 0.0
whiteBalanceBlue = 0.0

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

lcdState = 4

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
            <li>Sharpness: <span id="sharpness"></span></li>
            <li>Analogue Gain: <span id="analogueGain"></span></li>
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
                        document.getElementById('analogueGain').textContent = data.analogueGain;
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
        return True
    except bluetooth.BluetoothError as e:
        return False

def send_messages(client_sock,var):
    flag = True
    while flag:
        try:
            print("MESSAGE SENT")
            client_sock.send(str(var)+"\n")
            flag = False
        except bluetooth.BluetoothError as e:
            flag = True

def input_processing(client_sock):
    #Serial read from esp32
    global lightRead, espInput, currVar, lightValue, sharpness, analogueGain, whiteBalanceRed, whiteBalanceBlue, servoBase, servoUpper,ledState, lcdState,controllerAlive
    parsing = False
    number_str = ""
    if espInput:
        print("Input => " + str(espInput))
        for char in espInput:
            if parsing and char.isdigit():
                    number_str += char
            if char == 'U' and espInput != None:
                currVar += 1
                currVar %= 8
                print("State: " + str(currVar))
                send_messages(client_sock,currVar)
                espInput = None
                break
            elif char == 'D' and espInput != None:
                currVar -= 1
                currVar %= 8
                print("State: " + str(currVar))
                send_messages(client_sock,currVar)
                espInput = None
                break
            elif char == 'S':
                parsing = True
                continue
            elif (char == 'L' or char == 'R') and espInput != None :
                match currVar:
                    case 0:
                        if char == 'L' and servoBase > 0:
                            servoBase -= 2
                        elif char == 'R' and servoBase < 180:
                            servoBase += 2
                        espInput = None
                    case 1:
                        if char == 'L' and servoUpper > 20:
                            servoUpper -= 2
                        elif char == 'R' and servoUpper < 160:
                            servoUpper += 2
                        espInput = None
                    case 2:
                        if char == 'L':
                            ledState -= 1
                        elif char == 'R':
                            ledState += 1
                        ledState = ledState%4
                        espInput = None
                    case 3:
                        if char == 'L':
                            lcdState -= 1
                        if char == 'R':
                            lcdState += 1
                        lcdState %= 4
                        espInput = None
                    case 4:
                        if char == 'L' and whiteBalanceRed > 0:
                            whiteBalanceRed -= 1
                        if char == 'R' and whiteBalanceRed < 11:
                            whiteBalanceRed += 1
                            espInput = None
                    case 5:
                        if char == 'L' and whiteBalanceBlue > 0:
                            whiteBalanceBlue -= 1
                        if char == 'R' and whiteBalanceBlue < 11:
                            whiteBalanceBlue += 1
                            espInput = None
                    case 6:
                        if char == 'L' and sharpness >= 0:
                            sharpness -= 1
                        if char == 'R' and sharpness < 17:
                            sharpness += 1
                            espInput = None
                    case _:
                        if char == 'L' and analogueGain > 1:
                            analogueGain -= 1
                        if char == 'R' and analogueGain < 13:
                            analogueGain += 1
                            espInput = None
                            
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

        print("LED set to react to => " + str(lightRead) + " light value.")
        print("LED power set to => " + str(lightValue))
        
        print("Camera settings set to: WB-" + str(whiteBalanceBlue) + " WR-" + str(whiteBalanceRed)
            + " sharpness-" + str(sharpness) + " analogueGain-" +str(analogueGain))

        picam2.set_controls({"Sharpness": sharpness, "AnalogueGain": analogueGain, "ColourGains": (whiteBalanceRed,whiteBalanceBlue)})
        controllerAlive -= 1


def bluetooth_control(): 
    global stop_threads, controllerAlive

    connected = False
    esp32_address = None

    while esp32_address is None:
        esp32_address = find_esp32_device(target_name="Wireless Controller ESP32")
        print("Controller found !")

    client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    
    def reconnect():
        global controllerAlive
        nonlocal client_sock, esp32_address, connected
        controllerAlive = 0
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
        controllerAlive -= 1
        try:
            if not connected or controllerAlive <= 0:
                reconnect()

            if not receive_messages(client_sock):
                connected = False
                reconnect()
            else:
                print(controllerAlive)
                input_processing(client_sock)

        except bluetooth.BluetoothError as e:
            connected = False
            reconnect()

    client_sock.close()

def lcdControler():
    global lcdState, servoBase, lightRead, whiteBalanceBlue, whiteBalanceRed, analogueGain, sharpness,stop_threads, executiveAlive,controllerAlive
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
        "analogueGain": analogueGain,
        "whiteBalanceRed": whiteBalanceRed,
        "whiteBalanceBlue": whiteBalanceBlue
    })

def executiveUnitControll():
    global executiveAlive, servoBase, servoUpper, lightValue, stop_threads, ser
    last_command = {"lightValue": None, "servoBase": None, "servoUpper": None}

    while not stop_threads:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting).decode('utf-8')
            executiveAlive = 250000  # Reset heartbeat counter
        
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


def cleanup():
    global stop_threads
    print("leaning up and shutting down...")
    
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