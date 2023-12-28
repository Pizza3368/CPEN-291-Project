from flask import Flask, render_template, request, redirect
import socket

app = Flask(__name__)
PORT = 777
HOST = "10.93.48.142"
ADDR = (HOST, PORT)
HEADER = 64
FORMAT = "utf-8"
webClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
webClient.connect(ADDR)


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    webClient.sendall(send_length)
    webClient.sendall(message)


def receive_reply(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    msg = ""
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
    return msg


@app.route("/", methods=["GET", "POST"])
def main():
    message = "web"
    schefeed = ["", "", ""]
    if request.method == 'POST':
        # The button was pressed
        if request.form.get('schedule') == 'schedule':
            message += " schedule"
            send(message)
            data = receive_reply(webClient)
            print(data)
            sche = data.split(" ")
            for n in range(len(sche)):
                schefeed[n] += sche[n]
            print(schefeed)
            return render_template("index.html", sfeed1time=schefeed[0], sfeed2time=schefeed[1], sfeed3time=schefeed[2])
        if request.form.get('feed') == 'feed':
            message += " feed"
        if request.form.get('clean') == 'clean':
            message += " clean"
        if request.form.get('play') == 'play on':
            message += " play on"
        if request.form.get('play') == 'play off':
            message += " play off"
        send(message)
    return render_template("index.html")


@app.route("/setting", methods=["GET", "POST"])
def setting():
    message = "web update"
    if request.method == 'POST':
        if request.form.get('submit_button') == 'Submit':
            message += " "
            message += request.form.get('numberOfTimes')
            message += " "
            if request.form.get('numberOfTimes') == '1':
                message += str(request.form.get('time1'))
            elif request.form.get('numberOfTimes') == '2':
                message += str(request.form.get('time1'))
                message += " "
                message += str(request.form.get('time2'))
            elif request.form.get('numberOfTimes') == '3':
                message += str(request.form.get('time1'))
                message += " "
                message += str(request.form.get('time2'))
                message += " "
                message += str(request.form.get('time3'))
            message += " "
            message += request.form.get('feedAmount')
            send(message)
            return redirect("/")
    return render_template("settingpage.html")


@app.route("/history", methods=["GET", "POST"])
def history():
    message = "web history"
    send(message)
    data = receive_reply(webClient)
    print(data)
    feedhistime = [" ", " ", " ", " ", " "]
    feedhisamount = [" ", " ", " ", " ", " "]
    cleanhistime = [" ", " ", " ", " ", " ", " "]
    text = data.split(" clean ")
    feedlist = text[0].split(" ")
    print(feedlist)
    cleanlist = text[1].split(" ")
    print(cleanlist)
    lenfeed = len(feedlist)
    lenclean = len(cleanlist)
    numfeed = int(feedlist[1])
    numclean = int(cleanlist[0])
    if numfeed > 5:
        for n in range(5):
            feedhistime[5 - n] += feedlist[lenfeed - 2 * n - 2]
            feedhisamount[5 - n] += feedlist[lenfeed - 2 * n - 1]
    elif numfeed > 0:
        for n in range(numfeed):
            feedhistime[n] += feedlist[lenfeed - 2 * n - 2]
            feedhisamount[n] += feedlist[lenfeed - 2 * n - 1]

    if numclean > 5:
        for n in range(5):
            cleanhistime[n] += cleanlist[lenclean - n]
    elif numclean > 0:
        for n in range(numclean):
            cleanhistime[n] += cleanlist[lenclean - n - 1]

    return render_template("history.html", feed1time=feedhistime[0], feed2time=feedhistime[1], feed3time=feedhistime[2],
                           feed4time=feedhistime[3], feed5time=feedhistime[4], feed1amount=feedhisamount[0],
                           feed2amount=feedhisamount[1], feed3amount=feedhisamount[2], feed4amount=feedhisamount[3],
                           feed5amount=feedhisamount[4], clean1time=cleanhistime[0], clean2time=cleanhistime[1],
                           clean3time=cleanhistime[2], clean4time=cleanhistime[3], clean5time=cleanhistime[4])


if __name__ == "__main__":
    app.run(debug=True, host="10.93.48.142", port=80)
