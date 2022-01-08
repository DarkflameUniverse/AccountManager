from flask import render_template, Blueprint, redirect, url_for, request, send_from_directory, make_response
from flask_user import login_required, current_user
import json, glob, os
from wand import image

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


@main_blueprint.route('/get_dds_as_png/<filename>')
def get_dds_as_png(filename):
    if filename.split('.')[-1] != 'dds':
        return (404, "NO")

    cache = f'app/cache/{filename.split(".")[0]}.png'

    if not os.path.exists(cache):
        root = 'app/luclient/res/'

        path = glob.glob(
            root + f'**/{filename}',
            recursive=True
        )[0]

        with image.Image(filename=path) as img:
            img.compression = "no"
            img.save(filename='app/cache/'+filename.split('.')[0] + '.png')

    return send_from_directory(
        'cache/',
        filename.split('.')[0] + '.png',
        mimetype='image/vnd.microsoft.icon'
    )


@main_blueprint.route('/get_dds/<filename>')
def get_dds(filename):
    if filename.split('.')[-1] != 'dds':
        return 404

    root = 'app/luclient/res/'

    dds = glob.glob(
        root + f'**/{filename}',
        recursive=True
    )[0]

    with open(dds, 'r', errors="ignore") as file:
        dds_data = file.read()

    response = make_response(dds_data)
    return response


