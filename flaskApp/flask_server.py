from flask import Flask, request, session, render_template
from flask_socketio import SocketIO, emit
from flask import app as application

app = Flask(__name__)
socketio = SocketIO(app)
app.static_folder = 'static'

@app.route('/', methods=['GET'])
def main_page():
    print(session)
    return render_template("mainPage.html")

@app.route('/pulldata', methods=['GET'])
def pull_data():
    data_out = {"s1": "4", "s2": "5", "s3": "7"}
    return data_out

def push_data():
    data_out = {"s1": "44", "s2": "55", "s3": "77"}
    socketio.emit("update", data_out)
