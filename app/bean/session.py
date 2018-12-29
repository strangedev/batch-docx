from bean import bean
from bean.bean import Bean, BeanCreator


class Session(Bean):

    bean_name = "session"
    bean_description = {
        "usergroup_id": "INTEGER",
        "auth_token": "TEXT",
        "last_active": "INTEGER"
    }

    def __init__(self, id):
        super().__init__(id)

    @property
    def usergroup_id(self):
        return super()._getMemberFromDb("usergroup_id")

    @usergroup_id.setter
    def usergroup_id(self, usergroup_id: str):
        super()._setMemberInDb("usergroup_id", usergroup_id)

    @property
    def auth_token(self):
        return super()._getMemberFromDb("auth_token")

    @auth_token.setter
    def auth_token(self, auth_token: str):
        super()._setMemberInDb("auth_token", auth_token)

    @property
    def last_active(self):
        return super()._getMemberFromDb("last_active")

    @last_active.setter
    def last_active(self, last_active: str):
        super()._setMemberInDb("last_active", last_active)


def new_session(usergroup_id, auth_token, last_active):
    return BeanCreator(Session).create(usergroup_id=usergroup_id, auth_token=auth_token, last_active=last_active)


def remove_session_by_usergroup(usergroup):

    cur = bean.get_db()
    cur.execute("DELETE FROM session WHERE usergroup_id = ?", [usergroup.id])
    cur.commit()