import socket
import threading
import time

# server info with pico
HEADER = 64
PORT = 443
SERVER = '10.93.48.142'
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
# control signals for pico
nextInst: str = "None"
currFoodWeight: float = 0.0
feedWightThreshold: float = 0.0
currTime: int = time.localtime()
feedSchdule: list = list()
feedHistory: list = list()
queryInterval: int = 10  # should have connection with pico within every 10 secs

# webpage update
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def handle_client(conn, addr):
    print(f"New connection {addr} connected")
    connected = True
    while connected:
        msg = conn.recv(HEADER).decode(FORMAT)
        print(msg)
        if msg != 0:
            command = msg.split()
    conn.close()


def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Active connection: {threading.activeCount() - 1}")


# interaction with pico W through socket + logic control
def sendInst(inst):
    pass


def updateWeight(weight):
    pass


print("Server is starting...")
start()

while True:
    pass

