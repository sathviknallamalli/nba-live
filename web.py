import time
import threading
import websocket

# Callbacks for handling WebSocket events
def on_open(ws):
    print("WebSocket connection opened.")
    # Send a test message to the echo server
    ws.send("Hello, WebSocket!")

def on_message(ws, message):
    print(f"Received message: {message}")
    # After receiving the echo message, you can close the connection

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed:", close_status_code, close_msg)


# Function to simulate running the WebSocket connection
def run_websocket():
    ws_uri = "wss://echo.websocket.org"  # Using the public echo WebSocket server
    ws = websocket.WebSocketApp(
        ws_uri,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# Start the WebSocket client in a separate thread
ws_thread = threading.Thread(target=run_websocket)
ws_thread.start()

# Allow the user to stop the client gracefully
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping WebSocket client...")
    ws_thread.join()  # Wait for the WebSocket thread to finish
