from threading import Thread, Lock
from dotenv import load_dotenv
from queue import Queue
import numpy as np
import requests
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
#base_url = "https://awsite.site"
base_url = "http://localhost:5100"
token = None

# arduino info
ard_info = {"port": "COM3", "baud": 57600}

data_queue = Queue(maxsize=100)
cal_queue = Queue()

# get a valid jwt for the server given a valid username and password
def login():
    global token
    login_url = f"{base_url}/api/auth"
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        token = response.json().get('token')
        return True
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False

# connects to arduino board
def ard_connect():
    try:
        ard = serial.Serial(port=ard_info.get("port"), baudrate=ard_info.get("baud"), timeout=.1)
        return ard
    except:
        print("No Arduino Connection")
        return None

# upload new data to the server with a post request
def post_worker():
    post_url = f"{base_url}/api/postdata"
    while True:
        try:

            # get data from queue
            data = data_queue.get()
            if data is None:
                break

            current_token = token
            headers = {
                "Authorization": f"Bearer {current_token}",
                "Content-Type": "application/json"}
            try:
                response = requests.post(post_url, json=data, headers=headers, timeout=5)
                if response.status_code == 401:
                    print("Token expired, re-authenticating...")
                    if login():
                        current_token = token
                        headers["Authorization"] = f"Bearer {current_token}"
                        response = requests.post(post_url, json=data, headers=headers, timeout=5)
                response.raise_for_status()

                # get calVal from res
                res = response.json()
                calVal = res.get("cal", 0)
                if calVal != 0:
                    cal_queue.put(calVal)

            except requests.exceptions.RequestException as e:
                print(f"Post error: {e}")
            data_queue.task_done()

        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(1)

# main loop
def loop():
    ard = ard_connect()
    if not login():
        print("f")
    oldVals = [0, 0, 0, 0]
    t = time.time()
    while True:

        # attempt reconnect to serial
        if ard is None:
            time.sleep(5)
            ard = ard_connect()
            continue

        # check for calVal to send
        try:
            while not cal_queue.empty():
                cal = cal_queue.get_nowait()
                ard.write(str(cal).encode('utf-8'))
                print(f"Sent cal value: {cal}")
        except:
            pass

        # reads the Serial until relevant data is found
        try:
            line = str(ard.readline())
            if line != "b''":
                values = [float(exp.group()) for exp in re.finditer(r"[-.0-9]+", str(line))]

                # check there is new data to post
                for i in range(1, len(values)):
                    if (abs(oldVals[i] - values[i]) >= 4) or (time.time() - t >= 1):
                        t = time.time()
                        
                        oldVals = values.copy()
                        data = {
                            's1': str(oldVals[1]),
                            's2': str(oldVals[2]),
                            's3': str(oldVals[3])}
                        print(data)

                        # add to queue
                        if not data_queue.full():
                            data_queue.put(data)
                        else:
                            print("Queue full, dropping old data")
                            try:
                                data_queue.get_nowait()
                                data_queue.put(data)
                            except:
                                pass
                        break

        except Exception as e:
            print(f"Read error: {e}")
            ard = None
            continue

# start both threads
post_thread = Thread(target=post_worker, daemon=True)
post_thread.start()
thread = Thread(target=loop)
thread.start()
thread.join()