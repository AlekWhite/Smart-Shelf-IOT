from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

class Item(db.Model):
    __tablename__ = "item"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    per_unit_weight = db.Column( db.Float, nullable=False)
    image_link = db.Column(db.String(500))
    shelf_items = db.relationship("ShelfItem", back_populates="item", cascade="all, delete")

class Shelf(db.Model):
    __tablename__ = "shelf"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    shelf_items = db.relationship("ShelfItem", back_populates="shelf", cascade="all, delete")

class ShelfItem(db.Model):
    __tablename__ = "shelf_item"
    id = db.Column(db.Integer, primary_key=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelf.id", ondelete="CASCADE"), nullable=False)
    item_name = db.Column(db.String(255), db.ForeignKey("item.name", ondelete="CASCADE"), nullable=False)
    count = db.Column(db.Integer, default=0, nullable=False)
    restock_count = db.Column(db.Integer, default=0)
    allowed = db.Column(db.Boolean, default=True, nullable=False) 
    shelf = db.relationship("Shelf", back_populates="shelf_items")
    item = db.relationship("Item", back_populates="shelf_items")

class LiveData(db.Model):
    __tablename__ = "live_data"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

