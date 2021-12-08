from flask import render_template, Blueprint, redirect, url_for, request, abort
from flask_user import login_required, current_user
from app.models import Account, AccountInvitation, PlayKey, db
from datatables import ColumnDT, DataTables
from app.forms import CreatePlayKeyForm, EditPlayKeyForm

play_keys_blueprint = Blueprint('play_keys', __name__)

# Key creation page

@play_keys_blueprint.route('/', methods=['GET'])
@login_required
def index():
    if current_user.gm_level != 9:
        abort(403)
        return
    return render_template('play_keys/index.html.j2')


@play_keys_blueprint.route('/create/<count>/<uses>', methods=['GET'], defaults={'count': 1, 'uses': 1})
@login_required
def create(count=1, uses=1):

    PlayKey.create(count=count, uses=uses)
    return redirect(url_for('play_keys.index',  message=f"Created {count} Play Key(s) with {uses} uses!"))


@play_keys_blueprint.route('/create/bulk', methods=('GET', 'POST'))
@login_required
def bulk_create():
    if current_user.gm_level != 9:
        abort(403)
        return
    form = CreatePlayKeyForm()
    if form.validate_on_submit():
        PlayKey.create(count=form.count.data, uses=form.uses.data)
        return redirect(url_for('play_keys.index'))

    return render_template('play_keys/bulk.html.j2', form=form)


@play_keys_blueprint.route('/delete/<id>', methods=('GET', 'POST'))
@login_required
def delete(id):
    if current_user.gm_level != 9:
        abort(403)
        return
    key = PlayKey.query.filter(PlayKey.id == id).first()
    associated_accounts = Account.query.filter(Account.play_key_id==id).all()
    if len(associated_accounts) > 0:
        return redirect(url_for('play_keys.index'))
    key.delete()
    return redirect(url_for('play_keys.index'))


@play_keys_blueprint.route('/edit/<id>', methods=('GET', 'POST'))
@login_required
def edit(id):
    if current_user.gm_level != 9:
        abort(403)
        return

    key = PlayKey.query.filter(PlayKey.id==id).first()
    form = EditPlayKeyForm()

    if form.validate_on_submit():
        key.key_uses = form.uses.data
        key.active = form.active.data
        key.save()
        return redirect(url_for('play_keys.index'))

    form.uses.data = key.key_uses
    form.active.data = key.active

    return render_template('play_keys/edit.html.j2', form=form, key=key)


@play_keys_blueprint.route('/view/<id>', methods=('GET', 'POST'))
@login_required
def view(id):
    if current_user.gm_level != 9:
        abort(403)
        return
    key = PlayKey.query.filter(PlayKey.id == id).first()
    accounts = Account.query.filter(Account.play_key_id==id).all()
    return render_template('play_keys/view.html.j2', key=key, accounts=accounts)


@play_keys_blueprint.route('/get', methods=['GET'])
@login_required
def get():
    if current_user.gm_level != 9:
        abort(403)
        return
    columns = [
        ColumnDT(PlayKey.id),
        ColumnDT(PlayKey.key_string),
        ColumnDT(PlayKey.key_uses),
        ColumnDT(PlayKey.created_at),
        ColumnDT(PlayKey.active),
    ]

    query = db.session.query().select_from(PlayKey)

    params = request.args.to_dict()

    rowTable = DataTables(params, query, columns)

    data = rowTable.output_result()
    for play_key in data["data"]:
        play_key["0"] = f"""
            <a role="button" class="btn btn-primary btn btn-block"
            href='{url_for('play_keys.view', id=play_key["0"])}'>
            View
            </a>
            <a role="button" class="btn btn-secondary btn btn-block"
            href='{url_for('play_keys.edit', id=play_key["0"])}'>
            Edit
            </a>
            <a role="button" class="btn btn-danger btn btn-block"
            href='{url_for('play_keys.delete', id=play_key["0"])}'>
            Delete
            </a>
        """
        if play_key["4"]:
            play_key["4"] = '''<h1 class="far fa-check-square text-success"></h1>'''
        else:
            play_key["4"] = '''<h1 class="far fa-times-circle text-danger"></h1>'''

    return data
