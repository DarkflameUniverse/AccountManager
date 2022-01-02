from flask import (
    render_template,
    Blueprint,
    redirect,
    url_for,
    request,
    abort,
    jsonify,
    send_from_directory,
    make_response,
    flash
)
from flask_user import login_required, current_user
import json
from datatables import ColumnDT, DataTables
import time
from app.models import Property, db, UGC, CharacterInfo, PropertyContent
from app.schemas import PropertySchema
from app import gm_level, query_cdclient

import zlib
import xmltodict
import xml.etree.ElementTree as ET

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
        {property_data.name if property_data.name else query_cdclient(
            'select DisplayDescription from ZoneTable where zoneID = ?',
            [property_data.zone_id],
            one=True
        )[0]}
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
        ColumnDT(Property.id),                  # 0
        ColumnDT(Property.owner_id),            # 1
        ColumnDT(Property.template_id),         # 2
        ColumnDT(Property.clone_id),            # 3
        ColumnDT(Property.name),                # 4
        ColumnDT(Property.description),         # 5
        ColumnDT(Property.privacy_option),      # 6
        ColumnDT(Property.mod_approved),        # 7
        ColumnDT(Property.last_updated),        # 8
        ColumnDT(Property.time_claimed),        # 9
        ColumnDT(Property.rejection_reason),    # 10
        ColumnDT(Property.reputation),          # 11
        ColumnDT(Property.zone_id),             # 12
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
            property_data["4"] = query_cdclient(
            'select DisplayDescription from ZoneTable where zoneID = ?',
            [property_data["12"]],
            one=True
        )

        if property_data["6"] == 0:
            property_data["6"] = "Private"
        elif property_data["6"] == 1:
            property_data["6"] = "Best Friends"
        else:
            property_data["6"] = "Public"

        property_data["8"] = time.ctime(property_data["8"])
        property_data["9"] = time.ctime(property_data["9"])

        if not property_data["7"]:
            property_data["7"] = '''<h2 class="far fa-times-circle text-danger"></h2>'''
        else:
            property_data["7"] = '''<h2 class="far fa-check-square text-success"></h2>'''

        property_data["12"] = query_cdclient(
            'select DisplayDescription from ZoneTable where zoneID = ?',
            [property_data["12"]],
            one=True
        )

    return data


@property_blueprint.route('/view_model/<id>', methods=['GET'])
@login_required
def view_model(id):
    ugc_data = UGC.query.filter(UGC.id==id).first()

    if current_user.gm_level < 3:
        if current_user.id != ugc_data.account_id:
            abort(403)
            return

    return render_template('ldd/ldd.html.j2', model_list=[id])


@property_blueprint.route('/view_lot/<id>', methods=['GET'])
@login_required
def view_lot(id):


    return render_template('ldd/ldd.html.j2', model_list=[])


property_center = {
    1150: "(-17, 432, -60)",
    1151: "(0, 455, -110)",
    1250: "(-16, 432,-60)",
    1251: "(0, 455, 100)",
    1350: "(-10, 432, -57)",
    1450: "(-10, 432, -77)"
}


@property_blueprint.route('/view_models/<id>', methods=['GET'])
@login_required
def view_models(id):
    property_content_data = PropertyContent.query.filter(PropertyContent.property_id==id).all()

    model_list = []
    for content in property_content_data:
        model_list.append(content.id)

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

@property_blueprint.route('/get_model/<id>', methods=['GET'])
@login_required
def get_model(id):
    content = PropertyContent.query.filter(PropertyContent.id==id).first()

    if content.lot == 14: # ugc model
        response = ugc(content)[0]
    else: # prebuild model
        response = prebuilt(content)[0]

    response.headers.set('Content-Type', 'text/xml')
    return response



@property_blueprint.route('/download_model/<id>', methods=['GET'])
@login_required
def download_model(id):
    content = PropertyContent.query.filter(PropertyContent.id==id).first()

    if content.lot == 14: # ugc model
        response, filename = ugc(content)
    else: # prebuild model
        response, filename = prebuilt(content)

    response.headers.set('Content-Type', 'attachment/xml')
    response.headers.set(
        'Content-Disposition',
        'attachment',
        filename=filename
    )
    return response


def ugc(content):
    ugc_data = UGC.query.filter(UGC.id==content.ugc_id).first()
    uncompressed_lxfml = zlib.decompress(ugc_data.lxfml)
    response = make_response(uncompressed_lxfml)
    return response, ugc_data.filename


def prebuilt(content):
    # translate LOT to component id
    # we need to get a type of 2 because reasons
    render_component_id = query_cdclient(
        'select component_id from ComponentsRegistry where component_type = 2 and id = ?',
        [content.lot],
        one=True
    )[0]
    # find the asset from rendercomponent given the  component id
    lxfml = query_cdclient('select render_asset from RenderComponent where id = ?',
        [render_component_id],
        one=True
    )

    if lxfml:
        lxfml = lxfml[0].split("\\\\")[-1].lower()
    else:
        return f"No lxfml for LOT {content.lot}"

    lxfml = f'app/luclient/res/brickmodels/{lxfml.split(".")[0]}.lxfml'
    with open(lxfml, 'r') as file:
        lxfml_data = file.read()

    tree = ET.fromstring(lxfml_data)
    for bone in tree.findall('.//Bone'):
        transformation = bone.get('transformation').split(',')
        # print(f"Bone ID: {bone.get('refID')} -- Transformation: {transformation}")

        # TODO: Figure out Rotation
        # quaternion = [content.rw, content.rx, content.ry, content.rz]
        # rotation = quaternion_rotation_matrix(quaternion)
        # for index in range(len(rotation)):
        #     transformation[index] = rotation[index]

        transformation[9] = float(transformation[9]) + content.x
        transformation[10] = float(transformation[10]) + content.y
        transformation[11] = float(transformation[11]) + content.z

        # print(f"Bone ID: {bone.get('refID')} -- Transformation: {transformation}")
        bone.set('transformation', ','.join(map(str,transformation)))

    response = make_response(ET.tostring(tree))

    return response, lxfml.split('/')[-1]


def quaternion_rotation_matrix(Q):
    """
    Covert a quaternion into a full three-dimensional rotation matrix.

    Input
    :param Q: A 4 element array representing the quaternion (q0,x,y,z)

    Output
    :return: A 3x3 element matrix representing the full 3D rotation matrix.
             This rotation matrix converts a point in the local reference
             frame to a point in the global reference frame.
    """
    # Extract the values from Q
    w = Q[0]
    x = Q[1]
    y = Q[2]
    z = Q[3]

    # 3x3 rotation matrix
    m = [
        [0,0,0],
        [0,0,0],
        [0,0,0]
    ]

    # First row of the rotation matrix
    m[0][0] = 2 * ((w * w) + (x * x)) - 1
    m[0][1] = 2 * ((x * y) - (w * z))
    m[0][2] = 2 * ((x * z) + (w * y))

    # Second row of the rotation matrix
    m[1][0] = 2 * ((x * y) + (w * z))
    m[1][1] = 2 * ((w * w) + (y * y)) - 1
    m[1][2] = 2 * ((y * z) - (w * x))

    # Third row of the rotation matrix
    m[2][0] = 2 * ((x * z) - (w * y))
    m[2][1] = 2 * ((y * z) + (w * x))
    m[2][2] = 2 * ((w * w) + (z * z)) - 1

    return m
