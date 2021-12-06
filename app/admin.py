from flask import render_template, Blueprint, redirect, url_for
from flask_user import login_required, roles_required
from app.models import User, UserInvitation, UsersRoles

admin_blueprint = Blueprint('admin', __name__)

# Key creation page
@admin_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.gm_level != 9:
        return redirect(url_for('main.data_download'))

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
        return render_template('admin/dashboard.html.j2', message="Successfully created {} keys!".format(key_count), keys=key_list, resources=resources)

    return render_template('admin/dashboard.html.j2', current_user=current_user, resources=resources)


@admin_blueprint.route('/load_activities', methods=['GET', 'POST'])
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
