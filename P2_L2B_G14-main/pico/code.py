import wifi
import socketpool
import ipaddress
import time
import os
import board
import analogio
import pwmio
from adafruit_motor import servo

# edit host and port to match server
HEADER = 64
PORT = 443
HOST = "10.93.48.142"
ADDR = (HOST, PORT)
FORMAT = "utf-8"
INTERVAL = 5

print("Connecting to wifi")
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
print("Create TCP Client Socket")
pool = socketpool.SocketPool(wifi.radio)
socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
print("Connecting to VM Server")
socket.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    socket.send(send_length)
    socket.send(message)

def receive_reply(conn):
    msg = ""
    length_buf = bytearray(HEADER)
    conn.recv_into(length_buf, HEADER)
    msg_length = length_buf.decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg_buf = bytearray(msg_length)
        conn.recv_into(msg_buf, msg_length)
        msg = msg_buf.decode(FORMAT)
    return msg

# create PWMOut objects
pwmFD = pwmio.PWMOut(board.GP16, duty_cycle=2 ** 15, frequency=70)
pwmPL = pwmio.PWMOut(board.GP17, duty_cycle=2 ** 15, frequency=70)

# Create servo objects, my_servo.
servoFD = servo.Servo(pwmFD)
servoFD.angle = 80
servoPL = servo.Servo(pwmPL)
servoPL.angle = 80

# Initialize analog input connected to weight sensor
pressureSensor = analogio.AnalogIn(board.GP27)

def calc_weight(sensorIn):
    w = sensorIn.value / 30000 * sensorIn.reference_voltage - 0.074
    if w < 0:
        w = 0
    return w

def drop_food(amount):
    print(f"drop food {amount}")

def update_play(act):
    print(f"play {act}")

def do_instruction(inst, act):
    if inst == "feed":
        drop_food(act)
    elif inst == "play":
        update_play(act)

# time related variables
last_instr_time = time.monotonic()

while True:
    now = time.monotonic()
    try:
    #  every 5 seconds, ping server & update temp reading
        if now > (last_instr_time + INTERVAL):
            last_instr_time = now
            weight = calc_weight(pressureSensor)
            print(f"Weight: {weight}")
            send("pico weight " + str(weight))
            send("pico instruction")
            # need to change
            instruction = receive_reply(socket)
            print(instruction)
            if instruction != "None":
                inst_list = instruction.split()
                do_instruction(inst_list[0], inst_list[1])

    except Exception as e:
        print(e)
        continue

