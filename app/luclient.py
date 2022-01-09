from flask import (
    Blueprint,
    send_file,
    g
)
from flask_user import login_required
import glob
import os
from wand import image

import sqlite3
import xml.etree.ElementTree as ET

luclient_blueprint = Blueprint('luclient', __name__)


@luclient_blueprint.route('/get_dds_as_png/<filename>')
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


@luclient_blueprint.route('/get_dds/<filename>')
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


@luclient_blueprint.route('/get_icon/<id>')
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


def get_cdclient():
    """Connect to CDClient from file system Relative Path

    Args:
        None
    """
    cdclient = getattr(g, '_cdclient', None)
    if cdclient is None:
        cdclient = g._database = sqlite3.connect('app/luclient/res/cdclient.sqlite')
    return cdclient


def query_cdclient(query, args=(), one=False):
    """Run sql queries on CDClient

    Args:
        query   (string)    : SQL query
        args    (list)      : List of args to place in query
        one     (bool)      : Return only on result or all results
    """
    cur = get_cdclient().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def translate_from_locale(trans_string):
    """Finds the string translation from locale.xml

    Args:
        trans_string   (string)    : ID to find translation
    """
    if not trans_string:
        return "INVALID STRING"

    locale = "app/luclient/locale/locale.xml"

    with open(locale, 'r') as file:
        locale_data = file.read()

    locale_file = ET.XML(locale_data)

    phrase = locale_file.find(f'.//phrase[@id="{trans_string}"]').find('.//translation[@locale="en_US"]').text

    return phrase
