from dotenv import load_dotenv
from threading import Thread
import requests
import numpy as np
import serial
import json
import time
import os
import re

# load web credentials
load_dotenv()
login_data = {
    'username': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD")}
base_url = "https://awsite.site"
token = None

# arduino info
ard_info = {"port": "COM3", "baud": 57600}

# get a valid jwt for the server given a valid username and password
def login():
    global token
    login_url = f"{base_url}/api/auth"
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        token = response.json().get('token')
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# connects to arduino board
def ard_connect():
    try:
        ard = serial.Serial(port=ard_info.get("port"), baudrate=ard_info.get("baud"), timeout=.1)
        return ard
    except:
        print("No Arduino Connection")
        return None

# upload new data to the server with a post request
def post_data(data):
    post_url = f"{base_url}/api/postdata"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"}
    try:
        response = requests.post(post_url, json=data, headers=headers)
        if response.status_code == 401:
            time.sleep(1)
            login()
            post_data(data)
        response.raise_for_status()

        # get calVal from res
        res = response.json()
        calVal = res.get("cal", 0)
        return calVal

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# main loop
def loop():
    ard = ard_connect()
    login()
    oldVals = [0, 0, 0, 0]
    t = time.time()

    while True:
        # attempt reconnect to serial
        if ard is None:
            time.sleep(5)
            ard = ard_connect()
            continue

        # reads the Serial until relevant data is found
        try:
            line = str(ard.readline())
            if line != "b''":

                values = [float(exp.group()) for exp in re.finditer(r"[-.0-9]+", str(line))]
                for i in range(1, len(values)):
                    if (abs(oldVals[i] - values[i]) >= 4) or (time.time() - t >= 1):
                        t = time.time()
                        
                        oldVals = values.copy()
                        data = {
                            's1': str(oldVals[1]),
                            's2': str(oldVals[2]),
                            's3': str(oldVals[3])}
                        print(data)

                        cal = post_data(data)
                        if cal != 0:
                            ard.write(str(cal).encode('utf-8'))
                        break
        except:
            print("Failed to read Arduino data")
            continue
        time.sleep(0.01)

thread = Thread(target=loop)
thread.start()
