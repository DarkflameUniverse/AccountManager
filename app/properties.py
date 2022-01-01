from flask import render_template, Blueprint, redirect, url_for, request, abort, jsonify, send_file, make_response, flash
from flask_user import login_required, current_user
import json
from datatables import ColumnDT, DataTables
import time
from app.models import Property, db, UGC, CharacterInfo, Zone, PropertyContent
from app.schemas import PropertySchema
from app import gm_level

import zlib
import xmltodict

property_blueprint = Blueprint('properties', __name__)

property_schema = PropertySchema()

@property_blueprint.route('/', methods=['GET'])
@login_required
@gm_level(3)
def index():
    return render_template('properties/index.html.j2')


@property_blueprint.route('/approve/<id>', methods=['GET'])
@login_required
@gm_level(3)
def approve(id):

    property_data =  Property.query.filter(Property.id == id).first()

    property_data.mod_approved = not property_data.mod_approved

    # If we approved it, clear the rejection reason
    if property_data.mod_approved:
        property_data.rejection_reason = ""

    flash(
        f"""Approved Property
        {property_data.name if property_data.name else Zone.query.filter(Zone.id==property_data.zone_id).first().name }
        from {CharacterInfo.query.filter(CharacterInfo.id==property_data.owner_id).first().name}""",
        "success"
    )
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


@property_blueprint.route('/get/<status>', methods=['GET'])
@login_required
@gm_level(3)
def get(status="all"):
    columns = [
        ColumnDT(Property.id),
        ColumnDT(Property.owner_id),
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

    query = None
    if status=="all":
        query = db.session.query().select_from(Property)
    elif status=="approved":
        query = db.session.query().select_from(Property).filter(Property.mod_approved==True)
    elif status=="unapproved":
        query = db.session.query().select_from(Property).filter(Property.mod_approved==False)
    else:
        raise Exception("Not a valid filter")


    params = request.args.to_dict()

    rowTable = DataTables(params, query, columns)

    data = rowTable.output_result()
    for property_data in data["data"]:
        id = property_data["0"]

        property_data["0"] = f"""
            <a role="button" class="btn btn-primary btn btn-block"
                href='{url_for('properties.view', id=id)}'>
                View
            </a>
        """

        if not property_data["7"]:
            property_data["0"] += f"""
                <a role="button" class="btn btn-success btn btn-block"
                    href='{url_for('properties.approve', id=id)}'>
                    Approve
                </a>
            """
        else:
            property_data["0"] += f"""
                <a role="button" class="btn btn-danger btn btn-block"
                    href='{url_for('properties.approve', id=id)}'>
                    Unapprove
                </a>
            """

        property_data["1"] = f"""
            <a role="button" class="btn btn-primary btn btn-block"
                href='{url_for('characters.view', id=property_data["1"])}'>
                {CharacterInfo.query.filter(CharacterInfo.id==property_data['1']).first().name}
            </a>
        """

        if property_data["4"] == "":
            property_data["4"] = f"{Zone.query.filter(Zone.id==property_data['12']).first().name}"

        if property_data["6"] == 0:
            property_data["6"] = "Private"
        elif property_data["6"] == 1:
            property_data["6"] = "Best Friends"
        else:
            property_data["6"] = "Public"

        property_data["8"] = time.ctime(property_data["8"])
        property_data["9"] = time.ctime(property_data["9"])
        property_data["12"] = Zone.query.filter(Zone.id==property_data["12"]).first().name

        if not property_data["7"]:
            property_data["7"] = '''<h2 class="far fa-times-circle text-danger"></h2>'''
        else:
            property_data["7"] = '''<h2 class="far fa-check-square text-success"></h2>'''

    return data


@property_blueprint.route('/view_ugc/<id>', methods=['GET'])
@login_required
def view_ugc(id):
    ugc_data = UGC.query.filter(UGC.id==id).first()

    if current_user.gm_level < 3:
        if current_user.id != ugc_data.account_id:
            abort(403)
            return

    return render_template('ldd/ldd.html.j2', model_list=[id])


property_center = {
    1150: "(-17, 432, -60)",
    1151: "(0, 455, -110)",
    1250: "(-16, 432,-60)",
    1251: "(0, 455, 100)",
    1350: "(-10, 432, -57)",
    1450: "(-10, 432, -77)"
}


@property_blueprint.route('/view_ugcs/<id>', methods=['GET'])
@login_required
def view_ugcs(id):
    property_content_data = PropertyContent.query.filter(PropertyContent.property_id==id).all()

    model_list = []
    for content in property_content_data:
        if content.ugc_id:
            model_list.append(content.ugc_id)

    if current_user.gm_level < 3:
        if current_user.id != ugc_data.account_id:
            abort(403)
            return

    return render_template(
        'ldd/ldd.html.j2',
        model_list=model_list,
        center=property_center[
            Property.query.filter(Property.id==id).first().zone_id
        ]
    )

@property_blueprint.route('/get_ugc/<id>', methods=['GET'])
@login_required
def get_ugc(id):
    ugc_data = UGC.query.filter(UGC.id==id).first()

    if current_user.gm_level < 3:
        if current_user.id != ugc_data.account_id:
            abort(403)
            return

    uncompressed_lxfml = zlib.decompress(ugc_data.lxfml)
    response = make_response(uncompressed_lxfml)
    response.headers.set('Content-Type', 'text/xml')
    return response
    # return jsonify(xmltodict.parse(uncompressed_lxfml))


@property_blueprint.route('/download_ugc/<id>', methods=['GET'])
@login_required
def download_ugc(id):
    ugc_data = UGC.query.filter(UGC.id==id).first()

    if current_user.gm_level < 3:
        if current_user.id != ugc_data.account_id:
            abort(403)
            return

    uncompressed_lxfml = zlib.decompress(ugc_data.lxfml)

    response = make_response(uncompressed_lxfml)
    response.headers.set('Content-Type', 'attachment/xml')
    response.headers.set(
        'Content-Disposition',
        'attachment',
        filename=ugc_data.filename
    )
    return response
