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
    MASS_FACTOR = 100  # after calibration 100units = 1g
    ALLOWED_DEV = int(MASS_FACTOR/4)  # used to decide of the sensor vals or stable or not

    def __init__(self, app):
        super(DataBuilder, self).__init__()
        self.app = app
        self.running_vals = {}
        self.running_states = {}
        self.weight_key = {}

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
                    self.weight_key[si.item.name] = si.item.per_unit_weight
                self.running_vals[s.name] = [em, 0, em]
                self.running_states[s.name] = Status(s.status)

    # check if sensor vals match allowed vals
    def anomaly_check(self, key):
        exp_mas = 0
        count = 1
        for s in Shelf.query.all():
            if s.name == key:
                for si in s.shelf_items:
                    count += si.count
                    exp_mas += si.item.per_unit_weight * si.count
        print(f"AC: rv:{self.running_vals[key][0]} em:{exp_mas} tol:{count}")
        return int(self.running_vals[key][0]) in range(int(exp_mas - (count * DataBuilder.MASS_FACTOR)),
                                                       int(exp_mas + (count * DataBuilder.MASS_FACTOR)))

    # update the db when the items on a shelf change
    def handle_val_event(self, key, delta):
        if self.running_states[key] not in (Status.HEALTHY, Status.ANOMALY):
            return
        print(f"DELT: on:{key} rv:{self.running_vals[key][0]} delt:{delta}")

        # check if the delta factors into k number of known masses
        sums = []
        delta_int = int(abs(delta) / DataBuilder.MASS_FACTOR)
        for s in Shelf.query.all():
            if s.name == key:
                for si in s.shelf_items:
                    if si.allowed:

                        count = 1
                        exp_val_int = int(si.item.per_unit_weight / DataBuilder.MASS_FACTOR)
                        while (abs(delta_int - exp_val_int) > 3) and (exp_val_int < 3 * delta_int):
                            print(f"{delta_int} - {exp_val_int} = {abs(delta_int - exp_val_int)}")
                            exp_val_int += int(si.item.per_unit_weight / DataBuilder.MASS_FACTOR)
                            count += 1

                        print(f"is {int(delta_int / 10)} = {int((si.item.per_unit_weight * count) / (10 * DataBuilder.MASS_FACTOR))}?")
                        if int((si.item.per_unit_weight*count) / (10*DataBuilder.MASS_FACTOR)) == int(delta_int/10):
                            sums.append({"name": si.item.name, "val": si.count + (int(delta / abs(delta)) * count)})
        print(sums)

        # add the new items to the db
        if len(sums) == 1:
            update_values = {"count": sums[0]["val"]}
            with self.app.app_context():
                shelf_id = db.session.execute(select(Shelf.id).where(Shelf.name == key)).scalar()
                if shelf_id:
                    exists_query = select(ShelfItem.id).where(ShelfItem.shelf_id == shelf_id, ShelfItem.item_name == sums[0]["name"])
                    shelf_item_id = db.session.execute(exists_query).scalar()
                    if shelf_item_id:
                        update_stmt = (update(ShelfItem)
                                       .where(ShelfItem.shelf_id == shelf_id,
                                              ShelfItem.item_name == sums[0]["name"])
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
            if (self.anomaly_check(key)) or (value is Status.OFFLINE):
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

            # pull raw data from the db
            stmt = text(f""" SELECT *
                             FROM live_data
                             WHERE timestamp >= NOW() - INTERVAL '{interval}'
                             ORDER BY timestamp DESC""")
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

    # main loop, run detect_events once a second
    def run(self):
        t = time.time()
        while True:
            if time.time() - t >= 1:
                self.detect_events()
                t = time.time()
            else:
                time.sleep(0.001)