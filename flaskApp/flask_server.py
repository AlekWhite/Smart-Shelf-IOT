from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import Flask, request, session, render_template, abort, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, update
from flask import app as application
from datetime import timedelta
from dotenv import load_dotenv
from threading import Thread
import secrets
import time
import json
import os

from model import User, Item, Shelf, ShelfItem, LiveData, db 

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
calVal = 0


# deliver main html page
@app.route('/', methods=['GET'])
def main_page():
    if 'user_id' in session:
        session.pop('user_id', None)
    print(session)
    return render_template("mainPage.html")

# login for the web-app clients 
@app.route('/auth_page', methods=['GET', 'POST'])
def auth_page():
    if request.method == 'GET':
        return render_template("authPage.html")
    print(request.form)
    un = request.form.get("Username")
    pw = request.form.get("Password")
    user = User.query.filter_by(username=un).first()
    if not user:
        print("noUser Found", flush=True)
        return json.dumps({"error": "Invalid credentials BAD-USER"}), 401
    if check_password_hash(user.password_hash, pw):
        session['user_id'] = user.id
        return redirect(url_for("manager_page"))
    return json.dumps({"error": "Invalid credentials"}), 401

# manager page can edit shelf data in the db
@app.route('/manager_page', methods=['GET', 'POST'])
def manager_page():
    update_values = {}
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))

    # pull calVal from form
    cal = request.form.get("cal")
    if cal:
        global calVal
        calVal = cal
        print(cal)

    # add new a allowed item to a shelf   
    shelfEdit = request.form.get("newItemShelf")
    if shelfEdit:
        itemEdit = request.form.get("newItem")
        shelfEdit = "s" + str(shelfEdit)
        update_values["allowed"] = True
    else:
        shelfEdit = request.form.get("shelfUpdate")
        itemEdit = request.form.get('itemUpdate')

    # edit the shelf_item data in the db 
    if shelfEdit and itemEdit:
        print(f"Edit item: Shelf: {shelfEdit} Item: {request.form.get('itemUpdate')}")

        # update count
        count = request.form.get("count")
        if count:
            update_values["count"] = int(count)

        # update restock_count
        restock_count = request.form.get("restock_count")
        if restock_count:
            update_values["restock_count"] = int(restock_count)

        # handle remove (set allowed=False)
        remove = request.form.get("remove")
        if remove:
            update_values["allowed"] = False

    # update db
    if update_values:
        shelf_id = db.session.execute(select(Shelf.id).where(Shelf.name == shelfEdit)).scalar()
        if not shelf_id:
            print(f"No shelf found with name '{shelfEdit}'")
        else:
            exists_query = select(ShelfItem.id).where( ShelfItem.shelf_id == shelf_id, ShelfItem.item_name == itemEdit)
            shelf_item_id = db.session.execute(exists_query).scalar()
            if not shelf_item_id:
                print(f"No shelf_item found for shelf '{shelfEdit}' and item '{itemEdit}'")
            update_stmt = (update(ShelfItem)
                            .where(ShelfItem.shelf_id == shelf_id, ShelfItem.item_name == itemEdit)
                            .values(**update_values))
            db.session.execute(update_stmt)
            db.session.commit()

    return render_template("managerPage.html")

# login for data senders 
@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    if not user:
        print("noUser Found", flush=True)
        return json.dumps({"error": "Invalid credentials BAD-USER"}), 401
    if check_password_hash(user.password_hash, data.get('password')):
        token = create_access_token(identity=str(user.id))
        return json.dumps({"token": token}), 200
    return json.dumps({"error": "Invalid credentials"}), 401

# get all items in the store from the db
@app.route('/api/items')
def get_items():
    if 'user_id' not in session:
        return json.dumps({"error": "Invalid credentials"}), 401
    items = Item.query.order_by(Item.name).all()
    out = [{"name": i.name,
            "image_link": i.image_link,
            "weight": i.per_unit_weight } for i in items]
    return json.dumps(out), 200, {"Content-Type": "application/json"}

# get all display data for each shelf
@app.route("/api/shelves", methods=["GET"])
def get_shelves():
    shelves = Shelf.query.all()
    shelves_data = []

    for s in shelves:
        shelf_obj = {
            "id": s.id,
            "name": s.name,
            "status": s.status,
            "items": []}

        for si in s.shelf_items:
            item = si.item
            shelf_obj["items"].append({
                "shelf_item_id": si.id,
                "name": si.item_name,
                "count": si.count,
                "restock_count": si.restock_count,
                "allowed": si.allowed,
                "per_unit_weight": item.per_unit_weight if item else None,
                "image_link": item.image_link if item else None})

        shelves_data.append(shelf_obj)
    return json.dumps({"shelves": shelves_data}), 200


# put new data into the db
@app.route('/api/postdata', methods=['POST'])
@jwt_required()
def update_dataset():
    global calVal

    # put data into the db
    data = request.get_json()
    try:
        new_live_data = LiveData(data=data)
        db.session.add(new_live_data)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving live data: {e}", flush=True)
        return json.dumps({"status": "error", "message": str(e)}), 500

    # send cal request in response
    calOut = calVal
    if calVal != 0:
        calVal = 0

    return json.dumps({"status": "success", "cal": calOut}), 200
