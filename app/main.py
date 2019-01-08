import os

from flask import Flask, g, request, redirect, current_app, render_template, json
from werkzeug.utils import secure_filename

import auth
import util
from bean import bean
from bean.manglermapping import ManglerMapping, mappings_by_template, \
    new_manglermapping, delete_manglermapping
from bean.session import Session, remove_session_by_usergroup
from bean.template import Template, templates_by_usergroup, new_template, \
    grant_access, revoke_access, \
    duplicate_template, delete_template
from bean.usergroup import UserGroup, all_usergroups, remove_usergroup, \
    usergroups_by_template
from mangler.databatch import Databatch
from mangler.mangler import Mangler

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "/app/upload"


@app.before_request
def setup():
    bean.BeanTableCreator(Template).register()
    bean.BeanRelationCreator(Template, UserGroup).register()
    bean.BeanTableCreator(UserGroup).register()
    bean.BeanTableCreator(ManglerMapping).register()
    bean.BeanTableCreator(Session).register()

    if not request.path.endswith("login"):

        if "auth_token" not in request.cookies:
            redirect_to_login = redirect("login")
            response = current_app.make_response(redirect_to_login)
            return response

        if not auth.is_authorized(request.cookies["auth_token"]):
            redirect_to_login = redirect("login")
            response = current_app.make_response(redirect_to_login)
            return response


def current_usergroup_id():
    if "auth_token" not in request.cookies:
        return -1

    auth_token = request.cookies["auth_token"]

    db = bean.get_db()
    res = db.execute("SELECT * FROM session WHERE auth_token = ?",
                     [auth_token]).fetchone()

    return -1 if res is None else res["usergroup_id"]


def current_username():
    return UserGroup(current_usergroup_id()).name


@app.teardown_appcontext
def close_connection(exception):
    auth.cleanup_old_sessions()

    db = getattr(g, '_database', None)

    if db is not None:
        db.close()


@app.route('/')
def hello_world():
    redirect_to_templates = redirect("templates")
    response = current_app.make_response(redirect_to_templates)
    return response


@app.route("/login")
def show_login():
    return render_template("login.html", err=False)


@app.route("/do_login", methods=['POST'])
def do_login():
    username = request.form.get("username", type=str)
    password = request.form.get("password", type=str)

    cur = bean.get_db().cursor()
    res = cur.execute("SELECT COUNT(*) AS count FROM usergroup").fetchone()
    print(res["count"])

    if res["count"] < 1:
        new_user = auth.register_usergroup(username, password)
        new_user.privilege = 1

    try:
        token = auth.authorize(username, password)

    except Exception as e:
        print(e)
        return render_template("login.html", err=True)

    redirect_to_index = redirect('templates')
    response = current_app.make_response(redirect_to_index)
    response.set_cookie('auth_token', value=token)
    return response


@app.route("/templates")
def show_templates():
    templates = templates_by_usergroup(current_usergroup_id())
    t_values = sorted(
        [(t.id, t.name, t.date_added, t.date_last_used) for t in templates],
        key=lambda x: x[1])
    return render_template(
        "templates.html",
        current_username=current_username(),
        templates=t_values,
        page="templates"
    )


@app.route("/upload", methods=["POST"])
def do_upload():
    if 'file' not in request.files:
        # print("No file parts from", request.remote_addr)
        return redirect("templates")

    file = request.files['file']

    if file.filename == '':
        # print("Empty file from", request.remote_addr)
        return redirect("templates")

    if file and file.filename.rsplit('.', 1)[1].lower().startswith("doc"):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        template = new_template(filename, file_path, current_usergroup_id())

    return redirect("templates")


@app.route("/template_detail")
def show_template_detail():
    template_id = request.args.get("id")
    template = Template(template_id)
    attributes = [
        ("Hinzugefügt am", template.date_added),
        ("Zuletzt verwendet am", template.date_last_used)
    ]

    all_mappings = mappings_by_template(template_id)
    mappings = [(m.id, m.name, m.date_added, m.date_last_used) for m in
                all_mappings]

    all_users = all_usergroups()
    users = [(u.id, u.name) for u in all_users]
    granted_users = [(u.id, u.name) for u in usergroups_by_template(template)]

    return render_template(
        "template_detail.html",
        current_username=current_username(),
        page="templates",
        users=users,
        granted_users=granted_users,
        template_id=template_id,
        name=template.name,
        attributes=attributes,
        mappings=mappings
    )


@app.route("/new_mapping")
def show_new_mapping():
    t_id = request.args.get("t_id")
    mapping = new_manglermapping(t_id, "Unbenannte Zuweisung")

    mapping.mappings_json = json.dumps(
        Mangler(Template(mapping.template_id)).mapping_template)
    mapping.replacements_json = "{}"

    return redirect("edit_mapping?m_id={}".format(mapping.id))


@app.route("/edit_mapping")
def show_edit_mapping():
    m_id = request.args.get("m_id")
    mapping = ManglerMapping(m_id)

    attributes = [
        ("Gehört zu Vorlage", Template(mapping.template_id).name),
        ("Hinzugefügt am", mapping.date_added),
        ("Zuletzt verwendet am", mapping.date_last_used)
    ]

    return render_template(
        "edit_mapping.html",
        current_username=current_username(),
        page="templates",
        mapping_id=mapping.id,
        name=mapping.name,
        attributes=attributes,
        mapping_items=list(json.loads(mapping.mappings_json).items()),
        replacements=list(map(
            lambda a: (a[0], a[1][0], a[1][1]),
            enumerate(json.loads(mapping.replacements_json).items())))
    )


@app.route("/save_mapping", methods=["POST"])
def do_save_mapping():
    # fetch mapping
    m_id = request.json["id"]
    mapping = ManglerMapping(m_id)

    # update mapping
    mapping.replace_mappings(request.json["map"])
   
    # update replacements
    mapping.replace_replacements(request.json['replace'])

    # update name of this mapping
    mapping.name = request.json["name"]


@app.route("/mangle", methods=["POST"])
def do_mangle():
    t_id = request.form.get("t_id")
    m_id = request.form.get("m_id")

    previous_page = redirect("template_detail?id={}".format(t_id))

    if 'file' not in request.files:
        # print("No file parts from", request.remote_addr)
        return previous_page

    file = request.files['file']

    if file.filename == '':
        # print("Empty file from", request.remote_addr)
        return previous_page

    if not file or not file.filename.rsplit('.', 1)[1].lower().startswith(
            "csv"):
        return previous_page

    batch_path = util.generate_temp_filepath()
    file.save(batch_path)

    template = Template(t_id)
    mangler = Mangler(template)
    mapping = ManglerMapping(m_id)

    template.date_last_used = util.today()
    mapping.date_last_used = util.today()

    outfiles = mangler.create(mapping, Databatch(batch_path))

    return previous_page


@app.route("/remove_mapping", methods=['POST'])
def do_remove_mapping():
    m_id = request.form.get("m_id")
    mapping = ManglerMapping(m_id)
    template = Template(mapping.template_id)
    delete_manglermapping(mapping)

    return redirect("template_detail?id={}".format(template.id))


@app.route("/users")
def show_users():
    all_users = all_usergroups()
    users = [(u.id, u.name, u.privilege) for u in all_users]

    return render_template(
        "users.html",
        current_username=current_username(),
        page="users",
        users=users
    )


@app.route("/new_user")
def show_new_user():
    current_user = UserGroup(current_usergroup_id())
    if current_user.privilege < 1:
        return redirect("users")

    return render_template(
        "new_user.html",
        current_username=current_username(),
        page="users"
    )


@app.route("/register_user", methods=["POST"])
def do_register_user():
    username = request.form.get("username")
    password = request.form.get("password")
    privilege = request.form.get("privilege")

    current_user = UserGroup(current_usergroup_id())
    if current_user.privilege < 1:
        return redirect("users")

    new_user = auth.register_usergroup(username, password)
    new_user.privilege = privilege

    return redirect("users")


@app.route("/edit_user")
def show_edit_user():
    usergroup = UserGroup(request.args.get("u_id"))

    current_user = UserGroup(current_usergroup_id())
    if current_user.privilege < 1:
        return redirect("users")

    return render_template(
        "edit_user.html",
        current_username=current_username(),
        page="users",
        id=usergroup.id,
        name=usergroup.name,
        privilege=usergroup.privilege
    )


@app.route("/update_user", methods=["POST"])
def do_update_user():
    current_user = UserGroup(current_usergroup_id())
    if current_user.privilege < 1:
        return redirect("users")

    u_id = request.form.get("u_id")
    name = request.form.get("name")
    password = request.form.get("password")
    privilege = request.form.get("privilege")

    usergroup = UserGroup(u_id)

    if name != usergroup.name:
        cur = bean.get_db().cursor()
        res = cur.execute("SELECT * FROM usergroup WHERE name = ?",
                          [name]).fetchone()

        if res is not None:
            return redirect("edit_user?u_id={}".format(u_id))

        usergroup.name = name

    if len(password) > 0:
        auth.update_password(usergroup, password)

    usergroup.privilege = privilege

    return redirect("users")


@app.route("/remove_user", methods=["POST"])
def do_remove_user():
    current_user = UserGroup(current_usergroup_id())
    if current_user.privilege < 1:
        return redirect("users")

    u_id = request.form.get("u_id")
    usergroup = UserGroup(u_id)
    remove_usergroup(usergroup)

    return redirect("users")


@app.route("/logout", methods=["POST"])
def do_logout():
    usergroup = UserGroup(current_usergroup_id())
    remove_session_by_usergroup(usergroup)

    return redirect("login")


@app.route("/grant_access")
def do_grant_access():
    u_id = request.args.get("u_id")
    t_id = request.args.get("t_id")

    template = Template(t_id)
    current_usergroup = UserGroup(current_usergroup_id())
    if template.owner != current_usergroup.id and current_usergroup.privilege < 1:
        return redirect("template_detail?id={}".format(t_id))

    grant_access(UserGroup(u_id), template)

    return redirect("template_detail?id={}".format(t_id))


@app.route("/revoke_access")
def do_revoke_access():
    u_id = request.args.get("u_id")
    t_id = request.args.get("t_id")

    template = Template(t_id)
    current_usergroup = UserGroup(current_usergroup_id())
    if template.owner != current_usergroup.id and current_usergroup.privilege < 1:
        return redirect("template_detail?id={}".format(t_id))

    revoke_access(UserGroup(u_id), template)

    return redirect("template_detail?id={}".format(t_id))


@app.route("/swap_template", methods=["POST"])
def do_swap_template():
    t_id = request.form.get("t_id")

    previous_page = redirect("template_detail?id={}".format(t_id))

    if 'file' not in request.files:
        return previous_page

    file = request.files['file']

    if file.filename == '':
        return previous_page

    if file and file.filename.rsplit('.', 1)[1].lower().startswith("doc"):

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(file_path):
            os.remove(file_path)

        file.save(file_path)

        class Dummy(object):
            def __init__(self, path):
                self.path = path

        existing_template = Template(t_id)
        existing_template.path = file_path
        existing_template.name = filename

        dummy_template = Dummy(file_path)
        mangler = Mangler(dummy_template)
        dummy_mapping = mangler.mapping_template

        for m in mappings_by_template(t_id):
            m.merge_from(dummy_mapping, keep_own_values=True,
                         exclusive_merge=True)

        return previous_page


@app.route("/duplicate_template", methods=["GET"])
def do_duplicate_template():
    t_id = request.args.get("id")
    template_to_duplicate = Template(t_id)

    current_user = UserGroup(current_usergroup_id())
    if current_user.privilege < 1 and current_user.id is not template_to_duplicate.owner:
        return redirect("templates")

    template_result = duplicate_template(template_to_duplicate)

    return redirect("template_detail?id={}".format(template_result.id))


@app.route("/dump", methods=["GET"])
def do_dump():
    res = ""

    for m in mappings_by_template(1):
        res += m.mappings_json + "\n"
        res += m.replacements_json + "\n\n"

    return res


@app.route("/delete_template", methods=["POST"])
def do_delete_template():
    t_id = request.form.get("t_id")

    template_to_delete = Template(t_id)

    current_user = UserGroup(current_usergroup_id())
    if current_user.privilege < 1 and current_user.id is not template_to_delete.owner:
        return redirect("templates")

    delete_template(template_to_delete)

    return redirect("templates")


if __name__ == '__main__':
    app.run()
