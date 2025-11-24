from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, update
from flask import app as application
import threading
import time

from model import User, Item, Shelf, ShelfItem, LiveData, db 


class DataBuilder(threading.Thread):

       def __init__(self, app, db):
              super(DataBuilder, self).__init__()
              self.app = app
              self.db = db
              self.newData = True
              self.socketio = socketio

              # clear live data from db on startup
              with self.app.app_context():
                     try:
                            self.db.session.execute(db.text("TRUNCATE TABLE live_data"))
                            self.db.session.commit()
                     except Exception as e:
                            self.db.session.rollback()

       def detect_change():
              raw_data = LiveData.query.all()
              for rd in raw_data:
                     print(f"{rd.timestamp}: {rd.data}")
              print("-------")

       def run(self):
              t = time.time()
              while True:
                     if (time.time()-t >= 1):
                            detect_change()
                            t = time.time()
                     else:
                            time.sleep(0.001)