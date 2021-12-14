from flask import render_template, Blueprint, redirect, url_for, request, abort
from flask_user import login_required, current_user
import json
from datatables import ColumnDT, DataTables
import datetime, time
from app.schemas import CharacterInfoSchema

character_blueprint = Blueprint('characters', __name__)

character_schema = CharacterInfoSchema()

@character_blueprint.route('/', methods=['GET'])
@login_required
def index():
    if current_user.gm_level < 3:
        abort(403)
        return
    return render_template('character/index.html.j2')


@character_blueprint.route('/approve_name/<id>/<action>', methods=['GET'])
@login_required
def approve_name(id, action):
    if current_user.gm_level < 3:
        abort(403)
        return

    character =  CharacterInfo.query.filter(CharacterInfo.id == id).first()

    if action == "approve":
        if character.pending_name:
            character.name = character.pending_name
            character.pending_name = ""
        character.needs_rename = False
    elif action == "rename":
        character.needs_rename = True

    character.save()
    return redirect(request.referrer if request.referrer else url_for("main.index"))


@character_blueprint.route('/view/<id>', methods=['GET'])
@login_required
def view(id):

    character_data = CharacterInfo.query.filter(CharacterInfo.id == id).first()

    if current_user.gm_level < 3:
        if character_data.account_id and character_data.account_id != current_user.id:
            abort(403)
            return

    if character_data == {}:
        abort(404)
        return

    return render_template('character/view.html.j2', character_data=character_data)


@character_blueprint.route('/get', methods=['GET'])
@login_required
def get():
    if current_user.gm_level < 3 :
        abort(403)
        return
    columns = [
        ColumnDT(CharacterInfo.id),
        ColumnDT(CharacterInfo.account_id),
        ColumnDT(CharacterInfo.name),
        ColumnDT(CharacterInfo.pending_name),
        ColumnDT(CharacterInfo.needs_rename),
        ColumnDT(CharacterInfo.last_login),
        ColumnDT(CharacterInfo.permission_map),
    ]

    query = db.session.query().select_from(CharacterInfo)

    params = request.args.to_dict()

    rowTable = DataTables(params, query, columns)

    data = rowTable.output_result()
    for character in data["data"]:
        id = character["0"]
        character["0"] = f"""
            <a role="button" class="btn btn-primary btn btn-block"
                href='{url_for('characters.view', id=id)}'>
                View
            </a>
        """

        if not character["4"]:
            character["0"] += f"""
            <a role="button" class="btn btn-danger btn btn-block"
                href='{url_for('characters.approve_name', id=id, action="rename")}'>
                Needs Rename
            </a>
        """

        if character["3"] or character["4"]:
            character["0"] += f"""
            <a role="button" class="btn btn-success btn btn-block"
                href='{url_for('characters.approve_name', id=id, action="approve")}'>
                Approve Name
            </a>
        """

        if character["4"]:
            character["4"] = '''<h1 class="far fa-check-square text-danger"></h1>'''
        else:
            character["4"] = '''<h1 class="far fa-times-circle text-success"></h1>'''

        character["5"] = time.ctime(character["5"])


    return data

