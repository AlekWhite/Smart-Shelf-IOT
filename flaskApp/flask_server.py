from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, request, session, render_template, abort, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask import app as application
from dotenv import load_dotenv
from threading import Thread
import secrets
import time
import json
import os

import data_builder
from model import users, db
from datetime import timedelta

# pull info from .env
load_dotenv()
db_url = os.getenv("DATABASE_URL")

# server setup
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.static_folder = 'static'
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
app.config['JWT_SECRET_KEY'] = secrets.token_urlsafe(32)
app.config['SQLALCHEMY_DATABASE_URI'] = secrets.token_urlsafe(32)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) 
db.init_app(app)
jwt = JWTManager(app)
socketio = SocketIO(app)

# deliver main html page
@app.route('/', methods=['GET'])
def main_page():
    print(session)
    return render_template("mainPage.html")

@app.route('/auth', methods=['POST'])
def auth():
    data = request.get_json()
    user = users.query.filter_by(username=data.get('username')).first()
    if not user:
        print("noUser Found", flush=True)
        return json.dumps({"error": "Invalid credentials BAD-USER"}), 401
    if check_password_hash(user.password_hash, data.get('password')):
        token = create_access_token(identity=str(user.id))
        return json.dumps({"token": token}), 200
    return json.dumps({"error": "Invalid credentials"}), 401

@app.route('/auth_page', methods=['GET', 'POST'])
def auth_page():
    if request.method == 'GET':
        return render_template("authPage.html")
    print(request.form)
    un = request.form.get("Username")
    pw = request.form.get("Password")
    user = users.query.filter_by(username=un).first()
    if not user:
        print("noUser Found", flush=True)
        return json.dumps({"error": "Invalid credentials BAD-USER"}), 401
    if check_password_hash(user.password_hash, pw):
        session['user_id'] = user.id
        return redirect(url_for("manager_page"))
    return json.dumps({"error": "Invalid credentials"}), 401

@app.route('/manager_page', methods=['GET'])
def manager_page():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template("managerPage.html")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth_page'))

# put new data into the db
@app.route('/postdata', methods=['POST'])
@jwt_required()
def update_dataset():
    # put data from request.get_json() in to the db
    data = request.get_json()
    data_builder.displayData = data
    print(get_jwt_identity(), flush=True)
    return json.dumps({"status": "success"}), 200

# send display data on request
@app.route('/pulldata', methods=['GET'])
def pull_data():
    return data_builder.displayData

# socket connection
@socketio.on('connect')
def connect():
    print('Client connected')

# polls the data_builder, updates clients when display data is new
def push_data_thread():
    while True:
        data_builder.update_display_data()
        if data_builder.newData:
            socketio.emit("update", data_builder.displayData)
        time.sleep(1)

# start loop in new thread
poll_loop = Thread(target=push_data_thread)
poll_loop.start()
