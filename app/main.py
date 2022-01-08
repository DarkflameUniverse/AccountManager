from flask import render_template, Blueprint, redirect, url_for, request, send_from_directory, make_response, send_file
from flask_user import login_required, current_user
import json, glob, os
from wand import image

from app.models import Account, AccountInvitation, CharacterInfo
from app.schemas import AccountSchema, CharacterInfoSchema
from app.luclient import query_cdclient

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
@login_required
def get_dds_as_png(filename):
    if filename.split('.')[-1] != 'dds':
        return (404, "NO")

    cache = f'cache/{filename.split(".")[0]}.png'

    if not os.path.exists("app/" + cache):
        root = 'app/luclient/res/'

        path = glob.glob(
            root + f'**/{filename}',
            recursive=True
        )[0]

        with image.Image(filename=path) as img:
            img.compression = "no"
            img.save(filename='app/cache/'+filename.split('.')[0] + '.png')

    return send_file(cache)


@main_blueprint.route('/get_dds/<filename>')
@login_required
def get_dds(filename):
    if filename.split('.')[-1] != 'dds':
        return 404

    root = 'app/luclient/res/'

    dds = glob.glob(
        root + f'**/{filename}',
        recursive=True
    )[0]

    return send_file(dds)


@main_blueprint.route('/get_icon/<id>')
@login_required
def get_icon(id):

    render_component_id = query_cdclient(
        'select component_id from ComponentsRegistry where component_type = 2 and id = ?',
        [id],
        one=True
    )[0]

    # find the asset from rendercomponent given the  component id
    filename = query_cdclient('select icon_asset from RenderComponent where id = ?',
        [render_component_id],
        one=True
    )[0]

    filename = filename.replace("..\\", "").replace("\\", "/")

    cache = f'cache/{filename.split("/")[-1].split(".")[0]}.png'

    if not os.path.exists("app/" + cache):
        root = 'app/luclient/res/'

        with image.Image(filename=f'{root}{filename}'.lower()) as img:
            img.compression = "no"
            img.save(filename=f'app/cache/{filename.split("/")[-1].split(".")[0]}.png')

    return send_file(cache)
