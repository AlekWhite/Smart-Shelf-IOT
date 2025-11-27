from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, update, text
import threading
import time
import numpy as np
from model import LiveData, Shelf, Item, db, ShelfItem
from enum import Enum
from math import gcd
from functools import reduce

class Status(Enum):
       HEALTHY = "HEALTHY"
       UNSTABLE = "UNSTABLE"
       OFFLINE = "OFFLINE"
       ANOMALY = "ANOMALY"

class DataBuilder(threading.Thread):
       MASS_FACTOR = 100 # after calibration 100units = 1g
       ALLOWED_DEV = int(MASS_FACTOR/4) 

       def __init__(self, app):
              super(DataBuilder, self).__init__()
              self.app = app
              self.running_vals = {}
              self.running_states = {}
    
              with self.app.app_context():

                     # clear old data from db on startup
                     try:
                            db.session.execute(db.text("TRUNCATE TABLE live_data"))
                            db.session.commit()
                     except Exception as e:
                            db.session.rollback()

                     # load data from db
                     for s in Shelf.query.all():
                            em = 0
                            for si in s.shelf_items:
                                   em += si.count * si.item.per_unit_weight
                            self.running_vals[s.name] = [em, 0, em]
                            self.running_states[s.name] = Status(s.status) 

       # check if sensor vals match allowed vals
       def anomaly_check(self, key, val):
              
              # get allowed mass values 
              k_values = []
              for s in Shelf.query.all():
                     if s.name == key:
                            for si in s.shelf_items:
                                   if si.allowed:
                                          k_values.append([int(si.item.per_unit_weight / (DataBuilder.MASS_FACTOR*10)), si.item.name])

              # get the stable sensor value 
              n = abs(int(val / (DataBuilder.MASS_FACTOR*10)))             
              if n == 0:
                     return [None]
              print(f"AC: rv:{n} factors:{k_values}")
                                 
              # if n factors into the allowed masses it passes 
              dp = [None] * (n + 1)
              dp[0] = {}
              for i in range(1, n + 1):
                     for val in k_values:
                            k = val[0]
                            if i >= k and dp[i - k] is not None:
                                   new_cofs = dp[i - k].copy()
                                   new_cofs[k] = new_cofs.get(k, 0) + 1
                                   dp[i] = new_cofs
                                   break

              # record the items and counts
              if dp[n] is None:
                     return False
              new_items = []
              for v in k_values:
                     val = 0
                     for k in dp[n]:
                            if k == v[0]:
                                   val = dp[n][k]
                     new_items.append((val, v[1]))
              return new_items
              
                                      
       # update the db when the items on a shelf change 
       def handle_val_event(self, key, delta):
              if self.running_states[key] not in (Status.HEALTHY, Status.ANOMALY):
                     return
              print(f"DELT: on:{key} rv:{self.running_vals[key][0]} delt:{delta}")

              # when sensor val is zero, set all item counts to zero
              if int(self.running_vals[key][0] / (DataBuilder.MASS_FACTOR*10)) == 0:
                     new_items = []
                     for s in Shelf.query.all():
                            if s.name == key:
                                   for si in s.shelf_items:
                                          if si.allowed:
                                                 new_items.append((0, si.item.name))
                     print(f"MMM: {new_items}")

              # else check if the delta factors into known weights
              else: 
                     new_items = self.anomaly_check(key, self.running_vals[key][0])
                     print(f"AAA: {new_items}")
                     if not new_items:
                            return

              

              # read to db to find what the new total count must be 
              for i in new_items:
                     name = i[1] 
                     update_values = {"count": i[0]}
                     
                     # add the new items to the db
                     with self.app.app_context():
                            shelf_id = db.session.execute(select(Shelf.id).where(Shelf.name == key)).scalar()
                            if shelf_id:     
                                   exists_query = select(ShelfItem.id).where(ShelfItem.shelf_id == shelf_id, ShelfItem.item_name == name)
                                   shelf_item_id = db.session.execute(exists_query).scalar()
                                   if shelf_item_id:                                   
                                          update_stmt = (update(ShelfItem)
                                                               .where(ShelfItem.shelf_id == shelf_id, ShelfItem.item_name == name)
                                                               .values(**update_values))
                                          db.session.execute(update_stmt)
                                          db.session.commit()

              # do an anomaly_check
              self.handle_state_event(key, Status.HEALTHY)
                           
       # update the db when a shelf status changes 
       def handle_state_event(self, key, value):
              oldVal = self.running_states[key]
              if (oldVal == value) and (value != Status.HEALTHY):
                     return
              
              # do anomaly_check before status update
              new_status = Status.ANOMALY
              if value is not Status.ANOMALY:
                     if (self.anomaly_check(key, self.running_vals[key][0])) or (value is Status.OFFLINE):
                            print(f"STAT: {key} OLD: {oldVal} NEW: {value}")
                            new_status = value
              else:             
                     print(f"STAT: {key} OLD: {oldVal} NEW: {Status.ANOMALY}")
         
              # update db with new status
              if new_status is not oldVal:
                     self.running_states[key] = new_status
                     with self.app.app_context():
                            update_values = {"status": new_status.value}
                            update_stmt = (update(Shelf)
                                                 .where(Shelf.name == key)
                                                 .values(**update_values))
                            db.session.execute(update_stmt)
                            db.session.commit() 
  
       # processes live data from the last 10 sec to detect new events on each shelf
       def detect_events(self):
              with self.app.app_context():

                     # rotate window size
                     interval = "1 seconds"
                     if int(time.time()) % 10 == 0:
                            interval = "10 seconds"
                            for key in self.running_vals:
                                   self.handle_val_event(key, -1)

                     # pull raw data from the db
                     stmt = text(f"""
                            SELECT *
                            FROM live_data
                            WHERE timestamp >= NOW() - INTERVAL '{interval}'
                            ORDER BY timestamp DESC
                            """)
                     raw_data = db.session.execute(stmt).fetchall()

                     # detect offline event
                     if len(raw_data) == 0: 
                            for k in self.running_vals:
                                   self.handle_state_event(k, Status.OFFLINE)
                            return

                     # for each shelf 
                     for k in raw_data[0][1]:

                            # find the average val and std of the new data
                            data = []
                            for rd in raw_data:
                                   data.append(float(rd[1][k]))
                            vals = np.array(data)
                            avg = np.mean(vals)
                            std = np.std(vals)
                            
                            # when sensor values are stable 
                            if std <= DataBuilder.ALLOWED_DEV:
                            
                                   # detect mass change event
                                   delta = avg.item() - self.running_vals[k][0]
                                   if abs(delta) >= DataBuilder.MASS_FACTOR:
                                          self.running_vals[k][0] = avg.item()
                                          self.handle_val_event(k, delta) 
                                          
                                   # detect sensor is stable event
                                   else:
                                          self.running_vals[k][1] = 0
                                          self.handle_state_event(k, Status.HEALTHY)
                                      
                            # detect sensor when starts to be unstable
                            else:
                                   self.running_vals[k][1] += 1
                                   if self.running_vals[k][1] >= 15:
                                          self.handle_state_event(k, Status.UNSTABLE)

       # main loop, run deltect_events once a second                         
       def run(self):
              t = time.time()
              while True:
                     if (time.time()-t >= 1):
                            self.detect_events()
                            t = time.time()
                     else:
                            time.sleep(0.001)