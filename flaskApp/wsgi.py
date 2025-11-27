import flask_server
from flask_server import app
from data_builder import DataBuilder

if __name__ == "__main__":
    data_b = DataBuilder(app)
    data_b.start()
    app.run(host="0.0.0.0", port="5100", debug=False)
    
