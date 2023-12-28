from flask import Flask, render_template, request, jsonify
import requests
import socket

app = Flask(__name__)

PORT = 443
HOST = "10.93.48.142"
ADDR = (HOST, PORT)
webClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
webClient.connect(ADDR)


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == 'POST':
        # The button was pressed
        if request.form.get('submit_button') == 'Submit':
            print("button pressed")
            message = "ok"
            webClient.sendall(message.encode('utf-8'))
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True, host="10.93.48.142", port=80)

