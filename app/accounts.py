from flask import render_template, Blueprint, redirect, url_for, request
from flask_user import login_required, current_user
import json
from datatables import ColumnDT, DataTables

from app.models import Account, AccountInvitation, db
from app.schemas import AccountSchema

accounts_blueprint = Blueprint('accounts', __name__)

account_schema = AccountSchema()

@accounts_blueprint.route('/', methods=['GET'])
@login_required
def index():
    if current_user.gm_level < 3:
        abort(403)
        return
    return render_template('accounts/index.html.j2')

@accounts_blueprint.route('/view/<id>', methods=['GET'])
@login_required
def view(id):
    if current_user.gm_level < 3:
        abort(403)
        return
    account_data = json.loads(
        account_schema.jsonify(
            Account.query.filter(Account.id == id).first()
        ).data
    )
    del account_data["password"]
    return render_template('accounts/view.html.j2', account_data=account_data)


@accounts_blueprint.route('/get', methods=['GET'])
@login_required
def get():
    if current_user.gm_level != 9:
        abort(403)
        return
    columns = [
        ColumnDT(Account.id),
        ColumnDT(Account.username),
        ColumnDT(Account.email),
        ColumnDT(Account.gm_level),
        ColumnDT(Account.locked),
        ColumnDT(Account.banned),
        ColumnDT(Account.mute_expire),
    ]

    query = db.session.query().select_from(Account)

    params = request.args.to_dict()

    rowTable = DataTables(params, query, columns)

    data = rowTable.output_result()
    for play_key in data["data"]:
        play_key["0"] = f"""
            <a role="button" class="btn btn-primary btn btn-block"
            href='{url_for('accounts.view', id=play_key["0"])}'>
            View
            </a>
        """
            #        <a role="button" class="btn btn-danger btn btn-block"
            # href='{url_for('acounts.delete', id=play_key["0"])}'>
            # Delete
            # </a>
        if play_key["4"]:
            play_key["4"] = '''<h1 class="far fa-check-square text-danger"></h1>'''
        else:
            play_key["4"] = '''<h1 class="far fa-times-circle text-success"></h1>'''

        if play_key["5"]:
            play_key["5"] = '''<h1 class="far fa-check-square text-danger"></h1>'''
        else:
            play_key["5"] = '''<h1 class="far fa-times-circle text-success"></h1>'''

        if play_key["6"]:
            play_key["6"] = '''<h1 class="far fa-check-square text-danger"></h1>'''
        else:
            play_key["6"] = '''<h1 class="far fa-times-circle text-success"></h1>'''


    return data

