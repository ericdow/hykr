# hykr :sunrise_over_mountains: :snake:

Web-based path planning in python

# Flask How-To

**using python3.9 for this, probably need at least python3.6
**for now: replace all python3 commands with python3.9

https://realpython.com/flask-by-example-part-1-project-setup/#creating-the-python-flask-example-application

// create virtual environment to play in, only do this first time
python3 -m venv venv

// activate the virtual environment
source venv/bin/activate

// install packages
python3 -m pip install Flask==1.1.2
python3 -m pip install flask-sijax

// dump python packages
python3 -m pip freeze > requirements.txt

// run it and view
flask run
xdg-open http://localhost:5000

// deactivate the virtual environment
deactivate

// to reinstall the requirements in the virtual environment
python3 -m pip install -r requirements.txt
