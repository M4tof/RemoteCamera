import bluetooth
import threading

def receive_messages(client_sock):
    """Thread function to continuously receive messages."""
    while True:
        try:
            data = client_sock.recv(1024).decode("utf-8")
            if not data:
                print("Connection closed by client.")
                break
            print(f"Client: {data}")
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

def start_bluetooth_chat():
    try:
        # Create a Bluetooth socket
        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        port = 1
        server_sock.bind(("", port))
        server_sock.listen(1)

        print("Waiting for connection...")
        client_sock, client_info = server_sock.accept()
        print(f"Connected to {client_info}")

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
        server_sock.close()
        print("Bluetooth server closed.")

if __name__ == "__main__":
    start_bluetooth_chat()
