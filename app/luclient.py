import sqlite3
import xml.etree.ElementTree as ET
from flask import g

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

    phrase = locale_file.find(f'.//phrase[@id="{trans_string}"]').find(f'.//translation[@locale="en_US"]').text

    return phrase
