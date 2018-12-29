import util
from bean import bean
from bean.manglermapping import mappings_by_template, ManglerMapping, new_manglermapping, delete_manglermapping
from bean.usergroup import UserGroup


def new_template(name, path, owner):
    cur = bean.get_db().cursor()
    cur.execute("INSERT INTO template (name, path, date_added, date_last_used, owner) VALUES (?, ?, ?, ?, ?)",
                [name, path, util.today(), "", owner])

    template = Template(cur.lastrowid)

    owner_usergroup = UserGroup(owner)
    grant_access(owner_usergroup, template)

    return template


def usergroups_by_template(template_id):
    cur = bean.get_db()
    result = cur.execute("SELECT usergroup_id AS u_id "
                         "FROM template_usergroup "
                         "WHERE template_id = ?", [template_id])
    return set([UserGroup(r["u_id"]) for r in result])


def templates_by_usergroup(usergroup_id):
    cur = bean.get_db()
    result = cur.execute("SELECT template.id AS t_id "
                         "FROM template JOIN template_usergroup "
                         "ON template_id = template.id "
                         "WHERE usergroup_id = ?", [usergroup_id])
    return [Template(r["t_id"]) for r in result]


def grant_access(usergroup, template):
    cur = bean.get_db()
    cur.execute("INSERT INTO template_usergroup (template_id, usergroup_id) VALUES (?, ?)", [template.id, usergroup.id])


def revoke_access(usergroup, template):
    cur = bean.get_db()
    cur.execute("DELETE FROM template_usergroup WHERE template_id = ? AND usergroup_id = ?", [template.id, usergroup.id])


def duplicate_template(template_to_duplicate):
    result_name = "{} Kopie".format(template_to_duplicate.name)
    result_path = template_to_duplicate.path
    result_owner = template_to_duplicate.owner

    result_template = new_template(result_name, result_path, result_owner)

    for usergroup in usergroups_by_template(template_to_duplicate.id):
        if usergroup.id == result_template.owner:
            continue

        grant_access(usergroup, result_template)

    for manglermapping in mappings_by_template(template_to_duplicate.id):
        duplicate_mapping = new_manglermapping(result_template.id, manglermapping.name)
        duplicate_mapping.mappings_json = manglermapping.mappings_json
        duplicate_mapping.replacements_json = manglermapping.replacements_json

    return result_template


def delete_template(template_to_delete):

    for usergroup in usergroups_by_template(template_to_delete.id):
        revoke_access(usergroup, template_to_delete)

    for manglermapping in mappings_by_template(template_to_delete.id):
        delete_manglermapping(manglermapping)

    cur = bean.get_db().cursor()
    cur.execute("DELETE FROM template "
                "WHERE id = ?", [template_to_delete.id])

    del template_to_delete


class Template(bean.Bean):
    bean_name = "template"
    bean_description = {
        "name": "TEXT",
        "path": "TEXT",
        "date_added": "TEXT",
        "date_last_used": "TEXT",
        "owner": "INTEGER"
    }

    def __init__(self, id: int):
        super().__init__(id)

    @property
    def name(self):
        return super()._getMemberFromDb("name")

    @name.setter
    def name(self, name: str):
        super()._setMemberInDb("name", name)

    @property
    def path(self):
        return super()._getMemberFromDb("path")

    @path.setter
    def path(self, name: str):
        super()._setMemberInDb("path", name)

    @property
    def usergroups(self):
        #print(self.id, type(self.id))
        results = bean.get_db().execute("SELECT * FROM template_usergroup WHERE template_id = (?)", [self.id])
        return [UserGroup(result["id"]) for result in results]

    def remove_usergroup(self, usergroup: UserGroup):
        bean.get_db().execute(
            "DELETE FROM template_usergroup WHERE template_id = (?) AND usergroup_id = (?)",
            self.id,
            usergroup.id
        )

    def add_usergroup(self, usergroup: UserGroup):
        if not all([usergroup.id != ug.id for ug in self.usergroups]):
            return

        bean.get_db().execute(
            "INSERT INTO template_usergroup (template_id, usergroup_id) VALUES ((?), (?))",
            self.id,
            usergroup.id
        )

    @property
    def date_added(self):
        return super()._getMemberFromDb("date_added")

    @date_added.setter
    def date_added(self, date_added: str):
        super()._setMemberInDb("date_added", date_added)

    @property
    def date_last_used(self):
        return super()._getMemberFromDb("date_last_used")

    @date_last_used.setter
    def date_last_used(self, date_last_used: str):
        super()._setMemberInDb("date_last_used", date_last_used)

    @property
    def owner(self):
        return super()._getMemberFromDb("owner")

    @owner.setter
    def owner(self, owner: str):
        super()._setMemberInDb("owner", owner)
