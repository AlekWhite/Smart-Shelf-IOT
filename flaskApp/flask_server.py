from flask import Flask, request, session, render_template
from flask import app as application

app = Flask(__name__)
app.static_folder = 'static'

@app.route('/', methods=['GET'])
def main_page():
    print(session)
    return render_template("mainPage.html")

@app.route('/pulldata', methods=['GET'])
def pull_data():
    data_out = {"s1": "4", "s2": "5", "s3": "7"}
    return data_out