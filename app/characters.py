from flask import render_template, Blueprint, redirect, url_for, request, abort, flash
from flask_user import login_required, current_user
import json
from datatables import ColumnDT, DataTables
import datetime, time
from app.models import CharacterInfo, db
from app.schemas import CharacterInfoSchema
from app import gm_level

character_blueprint = Blueprint('characters', __name__)

character_schema = CharacterInfoSchema()

@character_blueprint.route('/', methods=['GET'])
@login_required
@gm_level(3)
def index():
    return render_template('character/index.html.j2')


@character_blueprint.route('/approve_name/<id>/<action>', methods=['GET'])
@login_required
@gm_level(3)
def approve_name(id, action):
    character =  CharacterInfo.query.filter(CharacterInfo.id == id).first()

    if action == "approve":
        if character.pending_name:
            character.name = character.pending_name
            character.pending_name = ""
        character.needs_rename = False
        flash(
            f"Approved name {character.name}",
            "success"
        )
    elif action == "rename":
        character.needs_rename = True
        flash(
            f"Marked character {character.name} (Pending Name: {character.pending_name if character.pending_name else 'None'}) as needing Rename",
            "danger"
        )

    character.save()
    return redirect(request.referrer if request.referrer else url_for("main.index"))


@character_blueprint.route('/view/<id>', methods=['GET'])
@login_required
@gm_level(3)
def view(id):

    character_data = CharacterInfo.query.filter(CharacterInfo.id == id).first()

    if character_data == {}:
        abort(404)
        return

    if character_data.account_id and character_data.account_id != current_user.id:
        abort(403)
        return

    return render_template('character/view.html.j2', character_data=character_data)


@character_blueprint.route('/get/<status>', methods=['GET'])
@login_required
@gm_level(9)
def get(status):
    columns = [
        ColumnDT(CharacterInfo.id),
        ColumnDT(CharacterInfo.account_id),
        ColumnDT(CharacterInfo.name),
        ColumnDT(CharacterInfo.pending_name),
        ColumnDT(CharacterInfo.needs_rename),
        ColumnDT(CharacterInfo.last_login),
        ColumnDT(CharacterInfo.permission_map),
    ]

    query = None
    if status=="all":
        query = db.session.query().select_from(CharacterInfo)
    elif status=="approved":
        query = db.session.query().select_from(CharacterInfo).filter((CharacterInfo.pending_name == "") & (CharacterInfo.needs_rename == False))
    elif status=="unapproved":
        query = db.session.query().select_from(CharacterInfo).filter((CharacterInfo.pending_name != "") | (CharacterInfo.needs_rename == True))
    else:
        raise Exception("Not a valid filter")

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

