import flask_server
from flask_server import socketio, app

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port="5100", allow_unsafe_werkzeug=True, debug=False)
