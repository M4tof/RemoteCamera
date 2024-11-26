import serial
import threading

def receive_messages(serial_conn):
    """Thread function to continuously receive messages."""
    while True:
        try:
            data = serial_conn.readline().decode("utf-8").strip()
            if not data:
                print("Connection closed by client.")
                # break
            print(f"\nClient: {data}")
        except serial.SerialException as e:
            print(f"Error receiving data: {e}")
            break

def send_messages(serial_conn):
    """Thread function to continuously send messages."""
    while True:
        try:
            message = input("You: ")
            if message.lower() == "exit":
                print("Ending chat.")
                serial_conn.close()
                break
            serial_conn.write((message + "\n").encode("utf-8"))
        except serial.SerialException as e:
            print(f"Error sending data: {e}")
            break

def start_bluetooth_chat():
    try:
        # Open the RFCOMM connection using pySerial to /dev/rfcomm0
        serial_conn = serial.Serial("/dev/rfcomm0", baudrate=115200, timeout=1)
        print("Connected to ESP32 via RFCOMM.")

        print("You can now start chatting! Type 'exit' to end the chat.")

        # Create and start threads for sending and receiving messages
        receive_thread = threading.Thread(target=receive_messages, args=(serial_conn,))
        send_thread = threading.Thread(target=send_messages, args=(serial_conn,))
        
        receive_thread.start()
        send_thread.start()

        # Wait for both threads to finish
        receive_thread.join()
        send_thread.join()

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    finally:
        if serial_conn.is_open:
            serial_conn.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    start_bluetooth_chat()
