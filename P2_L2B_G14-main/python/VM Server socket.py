import socket
import threading
import time

# server info with pico
HEADER = 64
PORT = 443
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
INSTRUCTION_INTERVAL = 5

# control signals for pico
currInst: str = "None"
currFoodWeight: float = 10.0
maxFoodWeight: float = 5.0
feedSchdule: list = list() # (time, done?)
feedHistory: list = list() # (time, amount)
play: bool = False
play_status : str = "off"
manualFeed = False

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def time_transfer_day(localTime: time.struct_time):
    hour = localTime.tm_hour
    minute = localTime.tm_min
    second = localTime.tm_sec
    result = str(hour) + " " + str(minute) + " " + str(second)
    return result

def time_transfer_date(localTime: time.struct_time):
    year = localTime.tm_year
    month = localTime.tm_mon
    day = localTime.tm_mday
    hour = localTime.tm_hour
    minute = localTime.tm_min
    result = str(year) + " " + str(month) + " " + str(day) + " " + str(hour) + " " + str(minute)
    return result

def time_in_range_day(time1: str, time2: str):
    time1_list = time1.split()
    time2_list = time2.split()
    
    time_1 = int(time1_list[0])*3600 + int(time1_list[1])*60 + int(time1_list[2])
    time_2 = int(time1_list[0])*3600 + int(time2_list[1])*60 + int(time2_list[2])
    return abs(time_1 - time_2) <= INSTRUCTION_INTERVAL * 2

def reply(conn, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)

def update_inst():
    now: str = time_transfer_day(time.localtime())
    instruct = "None"
    global manualFeed
    if manualFeed:
        amount = maxFoodWeight - currFoodWeight
        instruct = "feed" + " " + str(amount)
        manualFeed = False
    else:
        feedThisTime: bool = False
        global feedSchdule
        for i in range(len(feedSchdule)):
            if time_in_range_day(feedSchdule[i][0], now) and not feedSchdule[i][1]:
                amount = maxFoodWeight - currFoodWeight
                instruct = "feed" + " " + str(amount)
                feedSchdule[i] = (feedSchdule[i][0], True)
                feedThisTime = True
                break
        if not feedThisTime:
            global play
            if play:
                instruct = "play" + " " + play_status
                play = False

    global currInst
    currInst = instruct

def sendInst(conn):
    update_inst()
    reply(conn, currInst)

def update_play(status):
    global play
    play = True
    global play_status
    play_status = status

def update_max_food(amount):
    global maxFoodWeight
    if float(amount) > 0:
        maxFoodWeight = float(amount)

def updateWeight(weight):
    global currFoodWeight
    currFoodWeight = weight

def updateSchedule(new_schedule: list, number: int):
    global feedSchdule
    feedSchdule = list()

    for i in range(number):
        time_list = new_schedule[i].split(":")
        hour = time_list[0]
        minute = time_list[1]
        second = "0"
        time = str(hour) + " " + str(minute) + " " + second
        feedSchdule.append((time, False))

def refreshSchedule():
    global feedSchdule
    for task in feedSchdule:
        task[1] = False

# interaction with pico W through socket + logic control
def handle_pico(conn, msg_list):
    command = msg_list[1]
    print(f"in pico thread, schedule {feedSchdule}")
    print(f"in pico thread, MaxWeight {maxFoodWeight}")
    if command == "instruction":
        sendInst(conn)
    elif command == "weight":
        w = float(msg_list[2])
        updateWeight(w)

def handle_web(conn,msg_list):
    command = msg_list[1]
    if command == "feed":
        global manualFeed
        manualFeed = True
    elif command == "update":
        number = int(msg_list[2])
        new_schedule: list = msg_list[3:-1]
        amount = msg_list[-1]
        updateSchedule(new_schedule, number)
        update_max_food(amount)
        print(f"in web thread, schedule {feedSchdule}")
        print(f"in web thread, MaxWeight {maxFoodWeight}")
    elif command == "history":
        reply(conn, feedHistory)
    elif command == "schdule":
        reply(conn, feedSchdule)
    elif command == "play":
        status = msg_list[2]
        update_play(status)

def handle_client(conn, addr):
    print(f"New connection {addr} connected")
    connected  = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            print(*msg)
            msg_list = msg.split()
            client_id = msg_list[0]
            if client_id == "pico":
                handle_pico(conn, msg_list)
            elif client_id == "web":
                handle_web(conn, msg_list)
            else:
                print("unknown connection device")           
    conn.close()

# server action
def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Active connection: {threading.activeCount() - 1}" )

print("Server is starting...")
start()
previousTime = time_transfer_date(time.localtime()).split

while True:
    currTime = time_transfer_date(time.localtime()).split
    if previousTime[0] != currTime[0] or previousTime[1] != currTime[1] or previousTime[2] != currTime[2]: 
        refreshSchedule()
