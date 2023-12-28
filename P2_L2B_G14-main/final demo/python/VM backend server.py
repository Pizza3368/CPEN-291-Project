import socket
import threading
import time

# server info with pico
HEADER = 64
PORT_PICO = 443
PORT_WEB = 777
SERVER = socket.gethostbyname(socket.gethostname())
ADDR_PICO = (SERVER, PORT_PICO)
ADDR_WEB = (SERVER, PORT_WEB)
FORMAT = "utf-8"
INSTRUCTION_INTERVAL = 5
MAX_HISTORY_RECORD = 5

# control signals for pico
currInst: str = "None"
currFoodWeight: float = 10.0
maxFoodWeight: float = 5.0
feedSchdule: list = list() # (str: time, bool: done) time in format: "hour minute"
feedHistory: list = list() # (str: time, str: amount) time in format: "year mon day hour minute"
cleanHistory: list = list() # (str: time) time in format: "year mon day hour minute"
play: bool = False
play_status : str = "off"
manualFeed = False
manualClean = False

server_pico = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_pico.bind(ADDR_PICO)

server_web = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_web.bind(ADDR_WEB)

previousTime:list = list()

def refreshSchedule():
    global feedSchdule
    for i in range(len(feedSchdule)):
        feedSchdule[i] = (feedSchdule[i][0],False)

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
    result = str(year) + "/" + str(month) + "/" + str(day) + "_" + str(hour) + ":" + str(minute)
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
    now = time.localtime()
    now_str: str = time_transfer_day(now)
    # for schedule refresh
    '''
    global previousTime
    currTime: list = time_transfer_date(now).split()
    if previousTime[0] != currTime[0] or previousTime[1] != currTime[1] or previousTime[2] != currTime[2]:
        previousTime = currTime 
        refreshSchedule()
    '''
    instruct = "None"
    global manualFeed
    global manualClean
    global feedHistory
    global cleanHistory
    manual: bool = False
    if manualFeed:
        amount = maxFoodWeight - currFoodWeight
        if amount < 0:
            amount = 0
        feedHistory.append((time_transfer_date(now), str(amount)))
        if len(feedHistory) > MAX_HISTORY_RECORD:
            feedHistory = feedHistory[-MAX_HISTORY_RECORD:] # only keeps the last n records 
        instruct = "feed" + " " + str(maxFoodWeight)
        manual = True
        manualFeed = False
    elif manualClean:
        cleanHistory.append(time_transfer_date(now))
        if len(cleanHistory) > MAX_HISTORY_RECORD:
            cleanHistory = cleanHistory[-MAX_HISTORY_RECORD:]
        instruct = "clean"
        manual = True
        manualClean = False
    
    if not manual: # shceduled feed
        global feedSchdule
        for i in range(len(feedSchdule)):
            if time_in_range_day(feedSchdule[i][0], now_str) and not feedSchdule[i][1]:
                amount = maxFoodWeight - currFoodWeight
                if amount >= 0:
                    amount = 0
                feedSchdule[i] = (feedSchdule[i][0], True)
                feedHistory.append((time_transfer_date(now), str(amount)))
                if len(feedHistory) > MAX_HISTORY_RECORD:
                    feedHistory = feedHistory[-MAX_HISTORY_RECORD:]
                instruct = "feed" + " " + str(maxFoodWeight)
                feedThisTime = True
                break

    global play
    if play:
        instruct = "play" + " " + play_status
        play = False

    global currInst
    currInst = instruct

def sendInst(conn):
    update_inst()
    print(f"To pico instrction: {currInst}")
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

def sendHistory(conn):
    msg = ""
    feedNum = len(feedHistory)
    msg += "feed "
    msg += str(feedNum)

    for i in range(feedNum):
        t_str = feedHistory[i][0]
        amount: str = feedHistory[i][1]
        msg += " "
        msg += t_str
        msg += " "
        msg += amount

    cleanNum = len(cleanHistory)
    msg += " clean "
    msg += str(cleanNum)
    for i in range(cleanNum):
        t_str = cleanHistory[i]
        msg += " "
        msg += t_str
    print(f"sendHistory {msg}")
    reply(conn, msg)

def sendSchedule(conn):
    msg = ""
    pairNum = len(feedSchdule)
    for i in range(pairNum):
        time_str_list = feedSchdule[i][0].split()
        msg += time_str_list[0]
        msg += ":"
        msg += time_str_list[1]
        if i != pairNum - 1 :
            msg += " "
    
    print(f"sendSchedule {msg}")
    reply(conn, msg)

# interaction with pico W through socket + logic control
def handle_pico(conn, msg_list):
    command = msg_list[1]
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
    elif command == "clean":
        global manualClean
        manualClean = True
    elif command == "update":
        number = int(msg_list[2])
        new_schedule: list = msg_list[3:-1]
        amount = msg_list[-1]
        updateSchedule(new_schedule, number)
        update_max_food(amount)
    elif command == "history":
        sendHistory(conn)
    elif command == "schedule":
        sendSchedule(conn)
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
    server_pico.listen()
    server_web.listen()
    pico_connected = False
    while True:
        if not pico_connected: 
            conn, addr = server_pico.accept()
            pico_connected = True
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"Active connection: {threading.activeCount() - 1}" )
        conn1, addr1 = server_web.accept()
        thread1 = threading.Thread(target=handle_client, args=(conn1, addr1))
        thread1.start()
        print(f"Active connection: {threading.activeCount() - 1}" )

print("Server is starting...")
previousTime = time_transfer_date(time.localtime()).split
start()
