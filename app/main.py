from flask import render_template, Blueprint, redirect, url_for, request, send_from_directory
from flask_user import login_required, current_user
import json, glob, os

from app.models import Account, AccountInvitation, CharacterInfo
from app.schemas import AccountSchema, CharacterInfoSchema

main_blueprint = Blueprint('main', __name__)

account_schema = AccountSchema()
char_info_schema = CharacterInfoSchema()

@main_blueprint.route('/', methods=['GET'])
def index():
    """Home/Index Page"""
    if current_user.is_authenticated:

        account_data = Account.query.filter(Account.id == current_user.id).first()

        return render_template(
            'main/index.html.j2',
            account_data=account_data
        )
    else:
        return render_template('main/index.html.j2')

@main_blueprint.route('/about')
def about():
    """About Page"""
    return render_template('main/about.html.j2')

@main_blueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(
        'static/logo/',
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@main_blueprint.route('/find_file/<file_format>/<filename>', methods=['GET'])
@login_required
def find_file_brickdb(file_format, filename):
    root = 'app/luclient/res/'

    file_loc = glob.glob(
        root + f'**/{filename}.{file_format}',
        recursive=True
    )[0] # which LOD folder to load from

    with open(file_loc, 'r', errors="ignore") as file:
        file_data = file.read()

    return send_from_directory(os.getcwd() + "/" + ("/".join(file_loc.split("/")[:-1])), file_loc.split("/")[-1])
