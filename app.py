from flask import Flask
from flask import request
import urllib.request
from elevation_data import *

app = Flask(__name__)

@app.route("/")
def index():
    otd = OpenTopoData()
    elev = otd.get_elevations([(-43.5,172.5), (27.6,1.98)])
    return str(elev)

'''
@app.route("/")
def index():
    celsius = request.args.get("celsius", "")
    return (
        """<form action="" method="get">
                <input type="text" name="celsius">
                <input type="submit" value="Convert">
            </form>"""
        + celsius
    )

@app.route("/<int:celsius>")
def fahrenheit_from(celsius):
    """Convert Celsius to Fahrenheit degrees."""
    fahrenheit = float(celsius) * 9 / 5 + 32
    fahrenheit = round(fahrenheit, 3)  # Round to three decimal places
    return str(fahrenheit)
'''

if __name__ == "__main__":
    # TODO: remove debug
    app.run("127.0.0.1", port=5000, debug=True)
