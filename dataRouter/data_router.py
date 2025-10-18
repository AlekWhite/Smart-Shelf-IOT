from dotenv import load_dotenv
import requests
import json
import os

# load credentials
load_dotenv()
login_data = {
    'username': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD")}

data = {
    's1': '545555555',
    's2': '213',
    's3': '3'}

# get a valid jwt for the server given a valid username and password
def login():
    login_url = "http://127.0.0.1:5100/auth"
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        return response.json().get('token')
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# upload new data to the server with a post request
def post_data(token):
    post_url = "http://127.0.0.1:5100/postdata"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"}
    try:
        response = requests.post(post_url, json=data, headers=headers)
        if response.status_code == 401:
            post_data(login())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


t = login()
post_data(t)

""" 
Use this code to get hashed passwords, then enter them into the db

from werkzeug.security import check_password_hash, generate_password_hash
hashed_pw = generate_password_hash("PW")
print(hashed_pw)
print(check_password_hash(t, "PE"))

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, password_hash)
VALUES ('UN', 'hash');
"""