from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask.wrappers import Response
from flask_login.utils import login_url
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from bcrypt import checkpw, hashpw, gensalt

import re
import random
import string
import hashlib
import time
import json

import resources as res

class Resources():
    def __init__(self) -> None:
        self.LOGO = res.LOGO or 'logo/logo.png'
        self.PRIVACY_POLICY = res.PRIVACY_POLICY
        self.TERMS_OF_USE = res.TERMS_OF_USE

resources = Resources()

# Application instance
app = Flask(__name__)

# SQL instance
db = SQLAlchemy()

# Login instance
login_manager = LoginManager()


class UserModel(UserMixin):
    def __init__(self, id, username, gm_level):
        self.id = id
        self.username = username
        self.gm_level = gm_level

    def __repr__(self):
        return '<User %r>' % self.username

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False


# Activity data
class Activity():
    def __init__(self, start, end, map_id):
        self.start = start
        self.end = end
        self.map_id = map_id

class CharacterLog():
    def __init__(self, character_id):
        self.character_id = character_id
        self.activity_log = [] # List of activities
        self.last_logout = 0
        self.last_activity = None

    def register_login(self, start, map_id):
        self.last_activity = Activity(start, None, map_id)

    def register_logout(self, end):
        if not self.last_activity:
            return
        self.last_activity.end = end
        self.activity_log.append(self.last_activity)
        self.last_activity = None

    def get_play_time(self):
        total_time = 0
        for activity in self.activity_log:
            total_time += activity.end - activity.start
        return total_time

    def get_play_time_during(self, start, end):
        total_time = 0
        for activity in self.activity_log:
            if activity.start >= start and activity.end <= end:
                total_time += activity.end - activity.start
        return total_time

    def get_play_time_during_in_map(self, start, end, map_id):
        total_time = 0
        for activity in self.activity_log:
            if activity.start >= start and activity.end <= end and activity.map_id == map_id:
                total_time += activity.end - activity.start
        return total_time
        

    def __repr__(self):
        return '<CharacterLog %r>' % self.character_id


class Dataset():
    def __init__(self, label, data, borderColor, borderWidth):
        self.label = label
        self.data = data
        self.borderColor = borderColor
        self.borderWidth = borderWidth

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)


class ActivityData():
    def __init__(self, labels, title, datasets):
        self.labels = labels
        self.title = title
        self.datasets = datasets
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

activitie_data = {}

# Color definitions per map_id, alpha always 1
map_colors = {
    # 1000: Gray
    1000: 'rgba(200, 200, 200, 1)',
    # 1100: Green
    1100: 'rgba(0, 255, 0, 1)',
    # 1200: Blue
    1200: 'rgba(54, 162, 235, 1)',
    # 1300: Dark Red
    1300: 'rgba(255, 99, 132, 1)',
    # 1400: Purple
    1400: 'rgba(153, 102, 255, 1)',
    # 1600: Orange
    1600: 'rgba(255, 204, 0, 1)',
    # 1700: Light Blue
    1700: 'rgba(75, 192, 192, 1)',
    # 1800: Light Red
    1800: 'rgba(102, 0, 204, 1)',
    # 1900: Yellow
    1900: 'rgba(255, 159, 64, 1)',
    # 2000: Black
    2000: 'rgba(0, 0, 0, 1)',
}


@app.route('/load_activities', methods=['GET', 'POST'])
@login_required
def load_activities():
    if current_user.gm_level != 9:
        abort(403)
        return

    global activitie_data

    connection = db.engine

    epoch_time = int(time.time())
    # Calculate the time 7 days ago
    last_time = epoch_time - (7 * 24 * 60 * 60)

    query = "SELECT character_id, activity, time, map_id FROM activity_log WHERE time > %s"

    result = connection.execute(query, (last_time)).all()

    # Get all unique characters, create a new CharacterLog for each and put it in a dictionary
    characters = {}
    for row in result:
        if row[0] not in characters:
            characters[row[0]] = CharacterLog(row[0])

    # Loop through the results, if activity = 0, then it's a login, if activity = 1, then it's a logout
    for row in result:
        if row[1] == 0:
            characters[row[0]].register_login(row[2], row[3])
        else:
            characters[row[0]].register_logout(row[2])

    # Create activity data for the last 7 days
    # Titled: Sessions in the last 7 days
    # Data: Number of sessions
    labels = []
    data = []
    for i in range(7):
        labels.append(time.strftime("%a", time.localtime(epoch_time - (i * 24 * 60 * 60))))
        data.append(0)
    
    for character in characters:
        character_data = characters[character]
        for activity in character_data.activity_log:
            index = (activity.start - last_time) // (24 * 60 * 60)
            data[index] += 1

    # Flip labels
    labels.reverse()

    # Insert the data into the dictionary
    activitie_data["sessions"] = ActivityData(labels, "Sessions in the last 7 days", [Dataset("Sessions", data, "rgba(255, 99, 132, 1)", 3)])

    # Create activity data for total play time over the last 7 days
    # Titled: Total play time in the last 7 days
    # Data: Total play time in seconds
    labels = []
    data = []
    for i in range(7):
        labels.append(time.strftime("%a", time.localtime(epoch_time - (i * 24 * 60 * 60))))
        data.append(0)

        # Get the play time for the current day
        for character in characters:
            character_data = characters[character]
            begin = epoch_time - ((i + 1) * 24 * 60 * 60)
            end = begin + (24 * 60 * 60)
            play_time = character_data.get_play_time_during(begin, end) / (60 * 60)
            data[i] += play_time
    
    # Flip labels and data
    labels.reverse()
    data.reverse()

    # Insert the data into the dictionary
    activitie_data["play_time"] = ActivityData(labels, "Total play time in the last 7 days", [Dataset("Play time", data, "rgba(255, 99, 132, 1)", 3)])

    # Create activity data for each unique map played in the last 7 days
    # Titled: Maps played in the last 7 days
    # Data: Number of times played
    labels = []
    maps = {} # { 'map_id': [...] }

    # Get all unique maps
    for character in characters:
        character_data = characters[character]
        for activity in character_data.activity_log:
            # If the map_id is not devicible by 100, skip it
            if activity.map_id % 100 != 0:
                continue

            if activity.map_id not in maps:
                maps[activity.map_id] = []
                # Make the array of length 7
                for i in range(7):
                    maps[activity.map_id].append(0)

    for i in range(7):
        labels.append(time.strftime("%a", time.localtime(epoch_time - (i * 24 * 60 * 60))))

        # Get the total time played in each map over this day
        for map_id in maps:
            begin = epoch_time - ((i + 1) * 24 * 60 * 60)
            end = begin + (24 * 60 * 60)
            for character in characters:
                character_data = characters[character]
                play_time = character_data.get_play_time_during_in_map(begin, end, map_id) / (60 * 60)
                maps[map_id][6 - i] += play_time
    
    # Flip labels and data
    labels.reverse()

    # Insert the data into the dictionary, one dataset per map
    datasets = []
    for map_id in maps:
        color = map_colors[map_id]
        datasets.append(Dataset(map_id, maps[map_id], color, 3))

    activitie_data["zone_play_time"] = ActivityData(labels, "Maps played in the last 7 days", datasets)


    # Return 200
    return "OK", 200


@app.route('/activity_data/<name>', methods=['GET', 'POST'])
@login_required
def activity_data(name):
    if current_user.gm_level != 9:
        abort(403)
        return

    global activitie_data

    # Get the entry from the dictionary
    # Convert it to json and return it
    # In the format of:
    # {
    #   "labels": [...]
    #   "title": "..."
    #   "datasets": [{...}, {...}]
    # }
    # Cannot use jsonify because it doesn't support the Dataset class
    return activitie_data[name].toJSON()
    


# User loader
@login_manager.user_loader
def load_user(user_id):
    connection = db.engine
    
    query = "SELECT name, gm_level FROM accounts WHERE id = %s;"

    account_result = connection.execute(query, (user_id)).fetchone()

    if account_result is None:
        return None

    return UserModel(user_id, account_result[0], account_result[1])


# Index route. Allow both GET and POST requests. Render the "account_creation" page.
@app.route('/activate', defaults={'key': None}, methods=['GET', 'POST'])
@app.route('/activate/<key>', methods=['GET', 'POST'])
def account_creation(key):
    # If we get a POST request, collect the form data:
    # play_key, account_name, account_password, & account_repeat_password
    if request.method == 'POST':
        play_key = request.form['play_key']
        account_name = request.form['account_name']
        account_password = request.form['account_password']
        account_repeat_password = request.form['account_repeat_password']
        agree = request.form['agree'] if 'agree' in request.form else False

        # If the user didn't agree to the terms, return an error.
        if not agree:
            return render_template('public/account_creation.html', error="You must agree to the Privacy Policy and Terms of Service to continue.", resources=resources)

        # If the passwords don't match, return an error.
        if account_password != account_repeat_password:
            return render_template('public/account_creation.html', error="Passwords don't match!", resources=resources)

        connection = db.engine

        # Check if the play_key is valid.
        query = "SELECT id, key_uses, active FROM play_keys WHERE key_string = %s"

        key_result = connection.execute(query, (play_key)).fetchone()

        # If the play key is not active, or keyUses is 0, return an error.
        if not key_result or key_result['active'] == False or key_result['key_uses'] == 0:
            return render_template('public/account_creation.html', error="Invalid play key!", resources=resources)

        # Check if the username only contains alphanumeric characters, no spaces, or special characters.
        if not re.match("^[A-Za-z0-9_-]*$", account_name):
            return render_template('public/account_creation.html', error="Username contains invalid characters!", resources=resources)

        # Check if the username is no more than 32 characters long.
        if len(account_name) > 32:
            return render_template('public/account_creation.html', error="Username is too long!", resources=resources)
        
        # Check if the username is already taken.
        query = "SELECT COUNT(*) FROM accounts WHERE name = %s;"

        username_taken = connection.execute(query, (account_name))

        # If the username is taken, return an error.
        if username_taken.fetchone()[0] > 0:
            return render_template('public/account_creation.html', error="Username already taken!", resources=resources)

        # Decrement keyUses from the play_keys table by id.
        query = 'UPDATE play_keys SET key_uses = ' + str(key_result['key_uses'] - 1) + ' WHERE id = ' + str(key_result['id']) + ';'

        connection.execute(query)

        # Hash the password.
        password_hash = hashpw(account_password.encode('utf-8'), gensalt(prefix=b"2a"))

        # Insert the new account into the database. 
        query = 'INSERT INTO accounts (name, password, play_key_id) VALUES (%s, %s, ' + str(key_result['id']) + ');'

        connection.execute(query, (account_name, password_hash))

        # Notify the user of the successful account creation.
        return render_template('public/account_creation.html', message="Successfully created account '{}'!".format(account_name), resources=resources)

    key = key if key else ""

    return render_template('public/account_creation.html', key=key, resources=resources)


@login_manager.unauthorized_handler
def unauthorized_redirect():
    return redirect(url_for('login'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.gm_level == 9:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('data_download'))

    if request.method == 'POST':
        username = request.form['account_name']
        password = request.form['account_password']
        remember_me = request.form['remember_me'] if 'remember_me' in request.form else False

        # Check if the username is valid.
        connection = db.engine
        
        query = "SELECT id, password, gm_level FROM accounts WHERE name = %s;"

        account_result = connection.execute(query, (username)).fetchone()

        # If the username is not valid, return an error.
        if not account_result:
            return render_template('private/login.html', error="Incorrect username or password!", resources=resources)

        password_hash = account_result['password']
        gm_level = account_result['gm_level']

        # Support the old password style
        old_password = hashlib.sha512((password + username).encode('utf-8')).hexdigest()

        try:
            # If the password doesn't match the account name, return an error.
            if old_password != password_hash and not checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return render_template('private/login.html', error="Incorrect username or password!", resources=resources)
        except:
            return render_template('private/login.html', error="Incorrect username or password!", resources=resources)

        # Login user
        login_user(UserModel(account_result['id'], username, gm_level), remember=remember_me)
    
        # Redirect to the dashboard.
        if gm_level == 9:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('data_download'))
    
    return render_template('private/login.html', resources=resources)


# Data download page
@app.route('/data_download', methods=['GET', 'POST'])
@login_required
def data_download():
    if request.method == 'POST':
        # Get the data from the form.
        character_name = request.form['character_name']

        # Check if the character exists.
        connection = db.engine

        query = "SELECT id FROM charinfo WHERE name = %s AND account_id = %s;"

        character_result = connection.execute(query, (character_name, current_user.id)).fetchone()

        # If the character doesn't exist, return an error.
        if not character_result:
            return render_template('private/data_download.html', error="Character '{}' does not exist!".format(character_name), resources=resources)

        # Get the character's data.
        query = "SELECT xml_data FROM charxml WHERE id = %s;"
    
        xml_data = connection.execute(query, (character_result['id'])).fetchone()

        # If the character doesn't have any data, return an error.
        if not xml_data:
            return render_template('private/data_download.html', error="Character '{}' does not have any data!".format(character_name), resources=resources)

        # Return the character's data.
        return Response(xml_data['xml_data'], mimetype='text/xml', headers={"Content-disposition": "attachment; filename=" + character_name + ".xml"})

    return render_template('private/data_download.html', resources=resources)


# Key creation page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.gm_level != 9:
        return redirect(url_for('data_download'))

    if request.method == 'POST':
        connection = db.engine

        key_count = request.form['key_count']

        # Generate keys in the format AAAA-AAAA-AAAA-AAAA. 4 segments of uppercase letters and numbers.
        key_list = []
        for i in range(int(key_count)):
            key = ""

            for j in range(4):
                key += ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-'

            # Remove last dash
            key = key[:-1]

            key_list.append(key)

        # Insert the keys into the database.
        for key in key_list:
            query = "INSERT INTO play_keys (key_string, active) VALUES (%s, 1);"
            connection.execute(query, (key))

        # Notify the user of the successful key creation.
        return render_template('private/dashboard.html', message="Successfully created {} keys!".format(key_count), keys=key_list, resources=resources)

    return render_template('private/dashboard.html', current_user=current_user, resources=resources)


"""
App configuration

Some properties are in env variables.
"""

from os import getenv


def run_app():

    secret_key = getenv('SECRET_KEY')
    db_url = getenv('DB_URL')

    # If either of the env variables are not set, attempt to read them from credentials.py.
    if not secret_key or not db_url:
        from credentials import SECRET_KEY, DB_URL

        secret_key = SECRET_KEY
        db_url = DB_URL

    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    # Setup SQL
    db.init_app(app)

    # Setup Login
    login_manager.init_app(app)

    # Setup Bootstrap
    Bootstrap(app)

    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    run_app()