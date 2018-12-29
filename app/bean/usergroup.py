from bean import bean
from bean.bean import Bean, BeanCreator
from bean.session import remove_session_by_usergroup


class UserGroup(Bean):

    bean_name = "usergroup"
    bean_description = {
        "name": "TEXT",
        "password_salt": "TEXT",
        "password_hash": "TEXT",
        "privilege": "INTEGER"
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
    def password_salt(self):
        return super()._getMemberFromDb("password_salt")

    @password_salt.setter
    def password_salt(self, password_salt: str):
        super()._setMemberInDb("password_salt", password_salt)

    @property
    def password_hash(self):
        return super()._getMemberFromDb("password_hash")

    @password_hash.setter
    def password_hash(self, password_hash: str):
        super()._setMemberInDb("password_hash", password_hash)

    @property
    def privilege(self):
        return super()._getMemberFromDb("privilege")

    @privilege.setter
    def privilege(self, privilege: str):
        super()._setMemberInDb("privilege", privilege)


def new_usergroup(name, password_salt, password_hash):
    return BeanCreator(UserGroup).create(
        name=name,
        password_salt=password_salt,
        password_hash=password_hash,
        privilege=0
    )


def all_usergroups():

    cur = bean.get_db().cursor()
    res = cur.execute("SELECT * FROM usergroup")

    return [UserGroup(r["id"]) for r in res]


def remove_usergroup(usergroup):

    remove_session_by_usergroup(usergroup)

    cur = bean.get_db()
    cur.execute("DELETE FROM usergroup WHERE id = ?", [usergroup.id])
    cur.commit()


def usergroups_by_template(template):

    cur = bean.get_db().cursor()
    res = cur.execute("SELECT * FROM template_usergroup WHERE template_id = ?", [template.id])

    return [UserGroup(r["usergroup_id"]) for r in res]