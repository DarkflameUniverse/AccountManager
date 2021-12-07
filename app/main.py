from flask import render_template, Blueprint, redirect, url_for, request, send_from_directory
from flask_user import login_required, current_user
import os

from app.models import Account, AccountInvitation

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/', methods=['GET'])
def index():
    """Home/Index Page"""
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