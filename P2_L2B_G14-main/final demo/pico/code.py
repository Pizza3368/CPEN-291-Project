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
pwmFD = pwmio.PWMOut(board.GP17, duty_cycle=2 ** 15, frequency=70) # feed servo
pwmPL = pwmio.PWMOut(board.GP16, duty_cycle=2 ** 15, frequency=70) # play servo
pwmCL = pwmio.PWMOut(board.GP15, duty_cycle=2 ** 15, frequency=70) # clean servo
# Create servo objects, my_servo.
servoFD = servo.Servo(pwmFD)
servoFD.angle = 60
servoPL = servo.Servo(pwmPL) 
servoPL.angle = 60
servoCL = servo.Servo(pwmCL)
servoCL.angle = 60

# Initialize analog input connected to weight sensor
pressureSensor1 = analogio.AnalogIn(board.GP26)
pressureSensor2 = analogio.AnalogIn(board.GP27)
pressureSensor3 = analogio.AnalogIn(board.GP28) 

cleanArr = [60, 105, 150, 60]
playArr = [60, 150, 90, 180, 90, 150, 60]

# signals for servo control
doFeed = False
doClean = False
doPlay = False

lastCleanTime = time.monotonic()
lastPlayTime = time.monotonic()

cleanIndex = 0
playIndex = 0

maxFeedAmount = 0.0 

SERVO_INTERVAL = 1 

def calc_weight(sensorIn1, sensorIn2, sensorIn3):
    w1 = sensorIn1.value / 1000 * sensorIn1.reference_voltage - 10
    w2 = sensorIn2.value / 1000 * sensorIn2.reference_voltage - 10
    w3 = sensorIn3.value / 1000 * sensorIn3.reference_voltage - 10
    w = w1 + w2 + w3
    if w < 0:
        w = 0
    return w

def feed():
    global doFeed
    global maxFeedAmount
    if doFeed:
        w = calc_weight(pressureSensor1, pressureSensor2, pressureSensor3)
        print(f"in feed weight: {w}; max: {maxFeedAmount}")
        if  w < maxFeedAmount:
            servoFD.angle = 180 
        else:
            servoFD.angle = 90
            doFeed = False
        

def clean():
    now = time.monotonic()
    global doClean
    global cleanIndex
    global lastCleanTime 
    if doClean:
        if (now - lastCleanTime >= SERVO_INTERVAL):
            lastCleanTime = now
            servoCL.angle = cleanArr[cleanIndex]
            cleanIndex = cleanIndex + 1
            if cleanIndex >= len(cleanArr):
                cleanIndex = 0
                doClean = False

def play():
    now = time.monotonic()
    global doPlay
    global playIndex
    global lastPlayTime
    global lastPlayTime
    if doPlay:
        if (now - lastPlayTime >= SERVO_INTERVAL):
            lastPlayTime = now
            servoPL.angle = playArr[playIndex]
            playIndex = playIndex + 1
            if playIndex >= len(playArr): 
                playIndex = playIndex % len(playArr)

def handle_instruction(inst_list):
    global doFeed
    global doPlay
    global doClean
    global maxFeedAmount
    command = inst_list[0]
    if command == "feed":
        doFeed = True
        maxFeedAmount = float(inst_list[1])
    elif command == "play":
        if inst_list[1] == "on":
            doPlay = True
        elif inst_list[1] == "off":
            doPlay = False
    elif command == "clean":
        doClean = True
    elif command == "None":
        pass

# time related variables
last_instr_time = time.monotonic()

while True:
    now = time.monotonic()
    try:
    #  every 5 seconds, ping server & update weight reading and ask for instruction
        if now > (last_instr_time + INTERVAL): 
            last_instr_time = now
            weight = calc_weight(pressureSensor1, pressureSensor2, pressureSensor3)
            print(f"Weight: {weight}")
            send("pico weight " + str(weight))    
            send("pico instruction") 
            
            instruction = receive_reply(socket)
            print(instruction)
            inst_list = instruction.split()
            handle_instruction(inst_list)


    except Exception as e:
        print(e)
        continue

    feed()
    clean()
    play()

