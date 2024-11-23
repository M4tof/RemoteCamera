import bluetooth
import threading
import time

def receive_messages(client_sock):
    """Thread function to continuously receive messages."""
    while True:
        try:
            data = client_sock.recv(1024).decode("utf-8")
            if not data:
                print("Connection closed by client.")
                break
            print(f"\nClient: {data}")
        except bluetooth.BluetoothError as e:
            print(f"Error receiving data: {e}")
            break

def send_messages(client_sock):
    """Thread function to continuously send messages."""
    while True:
        try:
            message = input("You: ")
            if message.lower() == "exit":
                print("Ending chat.")
                client_sock.close()
                break
            client_sock.send(message + "\n")
        except bluetooth.BluetoothError as e:
            print(f"Error sending data: {e}")
            break

def find_esp32_device(target_name="ESP32_BT_Spammer"):
    """Function to scan for devices and find the ESP32."""
    print("Scanning for Bluetooth devices...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True)

    # Search for the ESP32 device by name
    for addr, name in nearby_devices:
        print(f"Found device: {name} ({addr})")
        if target_name in name:
            return addr  # Return the address if the ESP32 is found

    return None  # Return None if ESP32 is not found

def start_bluetooth_chat():
    try:
        # Find the ESP32 device
        esp32_address = find_esp32_device(target_name="ESP32_BT_Spammer")
        if esp32_address is None:
            print("ESP32 not found. Exiting...")
            return
        
        print(f"Found ESP32 device with address: {esp32_address}")
        # Create a Bluetooth socket and connect to the ESP32
        client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        client_sock.connect((esp32_address, 1))  # Connect to ESP32 RFCOMM port 1
        print(f"Connected to ESP32 at {esp32_address}")

        print("You can now start chatting! Type 'exit' to end the chat.")

        # Create and start threads for sending and receiving messages
        receive_thread = threading.Thread(target=receive_messages, args=(client_sock,))
        send_thread = threading.Thread(target=send_messages, args=(client_sock,))
        
        receive_thread.start()
        send_thread.start()

        # Wait for both threads to finish
        receive_thread.join()
        send_thread.join()

    except bluetooth.BluetoothError as e:
        print(f"Bluetooth error: {e}")
    finally:
        if 'client_sock' in locals() and client_sock:
            client_sock.close()
        print("Bluetooth server closed.")

if __name__ == "__main__":
    start_bluetooth_chat()
