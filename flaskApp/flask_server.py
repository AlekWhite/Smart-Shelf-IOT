from flask import Flask, request, session, render_template
from flask import app as application

app = Flask(__name__)
app.static_folder = 'static'