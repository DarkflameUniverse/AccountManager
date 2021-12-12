from flask import render_template, Blueprint, redirect, url_for, request, abort, jsonify, send_file, make_response
from flask_user import login_required, current_user
import json
from datatables import ColumnDT, DataTables
import datetime
from app.models import Property, db, UGC
from app.schemas import PropertySchema

import zlib
import xmltodict

property_blueprint = Blueprint('properties', __name__)

property_schema = PropertySchema()

@property_blueprint.route('/', methods=['GET'])
@login_required
def index():
    if current_user.gm_level < 3:
        abort(403)
        return
    return render_template('properties/index.html.j2')


@property_blueprint.route('/approve_name/<id>/<action>', methods=['GET'])
@login_required
def approve_name(id, action):
    if current_user.gm_level < 3:
        abort(403)
        return

    property_data =  Property.query.filter(Property.id == id).first()

    if action == "approve":
        if property_data.pending_name:
            property_data.name = property_data.pending_name
            property_data.pending_name = ""
        property_data.needs_rename = False
    elif action == "rename":
        property_data.needs_rename = True

    property_data.save()
    return redirect(request.referrer if request.referrer else url_for("main.index"))


@property_blueprint.route('/view/<id>', methods=['GET'])
@login_required
def view(id):

    property_data = Property.query.filter(Property.id == id).first()

    if current_user.gm_level < 3:
        if property_data.owner_id and property_data.owner.account_id != current_user.id:
            abort(403)
            return

    if property_data == {}:
        abort(404)
        return

    return render_template('properties/view.html.j2', property_data=property_data)


@property_blueprint.route('/get', methods=['GET'])
@login_required
def get():
    if current_user.gm_level < 3 :
        abort(403)
        return
    columns = [
        ColumnDT(Property.id),
        ColumnDT(Property.owner),
        ColumnDT(Property.template_id),
        ColumnDT(Property.clone_id),
        ColumnDT(Property.name),
        ColumnDT(Property.description),
        ColumnDT(Property.privacy_option),
        ColumnDT(Property.mod_approved),
        ColumnDT(Property.last_updated),
        ColumnDT(Property.time_claimed),
        ColumnDT(Property.rejection_reason),
        ColumnDT(Property.reputation),
        ColumnDT(Property.zone_id),
    ]

    query = db.session.query().select_from(Property)

    params = request.args.to_dict()

    rowTable = DataTables(params, query, columns)

    data = rowTable.output_result()
    for property_data in data["data"]:
        # id = property["0"]
        # property["0"] = f"""
        #     <a role="button" class="btn btn-primary btn btn-block"
        #         href='{url_for('property.view', id=id)}'>
        #         View
        #     </a>
        # """
        print(property_data["1"])
        # if not property["4"]:
        #     property["0"] += f"""
        #     <a role="button" class="btn btn-danger btn btn-block"
        #         href='{url_for('propertys.approve_name', id=id, action="rename")}'>
        #         Needs Rename
        #     </a>
        # """

        # if property["3"] or property["4"]:
        #     property["0"] += f"""
        #     <a role="button" class="btn btn-success btn btn-block"
        #         href='{url_for('propertys.approve_name', id=id, action="approve")}'>
        #         Approve Name
        #     </a>
        # """

        if not property_data["7"]:
            property_data["7"] = '''<h1 class="far fa-check-square text-danger"></h1>'''
        else:
            property_data["7"] = '''<h1 class="far fa-times-circle text-success"></h1>'''


    return data


@property_blueprint.route('/view_ugc/<id>', methods=['GET'])
@login_required
def view_ugc(id):
    ugc_data = UGC.query.filter(UGC.id==id).first()

    # if current_user.gm_level < 3:
    #     if current_user.id != ugc_data.account_id:
    #         abort(403)
    #         return

    return render_template('ldd/ldd.html.j2', id=id)

@property_blueprint.route('/get_ugc/<id>', methods=['GET'])
@login_required
def get_ugc(id):
    ugc_data = UGC.query.filter(UGC.id==id).first()


    # if current_user.gm_level < 3:
    #     if current_user.id != ugc_data.account_id:
    #         abort(403)
    #         return
    uncompressed_lxfml = zlib.decompress(ugc_data.lxfml)
    response = make_response(uncompressed_lxfml)
    response.headers.set('Content-Type', 'text/xml')
    return response
    # return jsonify(xmltodict.parse(uncompressed_lxfml))


@property_blueprint.route('/download_ugc/<id>', methods=['GET'])
@login_required
def download_ugc(id):
    ugc_data = UGC.query.filter(UGC.id==id).first()

    # if current_user.gm_level < 3:
    #     if current_user.id != ugc_data.account_id:
    #         abort(403)
    #         return

    uncompressed_lxfml = zlib.decompress(ugc_data.lxfml)

    response = make_response(uncompressed_lxfml)
    response.headers.set('Content-Type', 'attachment/xml')
    response.headers.set(
        'Content-Disposition',
        'attachment',
        filename='weedeater.lfxml'
    )
    return response
