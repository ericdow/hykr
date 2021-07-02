from flask import Flask, request, render_template, g
import os, sys, flask_sijax
from elevation_data import *

path = os.path.join('.', os.path.dirname(__file__), '../')
sys.path.append(path)

app = Flask(__name__)

# The path where you want the extension to create the needed javascript files
# DON'T put any of your files in this directory, because they'll be deleted!
app.config["SIJAX_STATIC_PATH"] = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')

# You need to point Sijax to the json2.js library if you want to support
# browsers that don't support JSON natively (like IE <= 7)
app.config["SIJAX_JSON_URI"] = '/static/js/sijax/json2.js'

flask_sijax.Sijax(app)

# example of passing array to a template
# TODO remove
@app.route("/pie")
def pie():
    # otd = OpenTopoData()
    # elev = otd.get_elevations([(-43.5,172.5), (27.6,1.98)])
    # return str(elev)
    values = [12, 19, 3, 5, 2, 3]
    labels = ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange']
    colors = ['#ff0000','#0000ff','#ffffe0','#008000','#800080','#FFA500']
    return render_template('pie.html', values=values, labels=labels, colors=colors)

# example of ijax enabled function - notice the `@Sijax.route` decorator
# TODO remove
@flask_sijax.route(app, "/sijax")
def hello_sijax():
    # Sijax handler function receiving 2 arguments from the browser
    # The first argument (obj_response) is passed automatically
    # by Sijax (much like Python passes `self` to object methods)
    def hello_handler(obj_response, hello_from, hello_to):
        obj_response.alert('Hello from %s to %s' % (hello_from, hello_to))
        obj_response.css('a', 'color', 'green')

    # Another Sijax handler function which receives no arguments
    def goodbye_handler(obj_response):
        obj_response.alert('Goodbye, whoever you are.')
        obj_response.css('a', 'color', 'red')

    if g.sijax.is_sijax_request:
        # The request looks like a valid Sijax request
        # Let's register the handlers and tell Sijax to process it
        g.sijax.register_callback('say_hello', hello_handler)
        g.sijax.register_callback('say_goodbye', goodbye_handler)
        return g.sijax.process_request()

    return render_template('sijax.html')

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
