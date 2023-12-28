from flask import Flask, render_template, request, redirect
import socket

app = Flask(__name__)
PORT = 443
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


@app.route("/", methods=["GET", "POST"])
def main():
    message = "web"
    if request.method == 'POST':
        # The button was pressed
        if request.form.get('feed') == 'feed':
            message += " feed"
            send(message)
            return render_template("index.html")
        if request.form.get('setting_button') == 'setting':
            return redirect("/setting")
        if request.form.get('submit') == 'submit':
            if request.form.get('play') == 'on':
                message += " play on"
            elif request.form.get('play') == 'off':
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
            print(message)
            return redirect("/")
    return render_template("settingpage.html")


if __name__ == "__main__":
    app.run(debug=True, host="10.93.48.142", port=80)
