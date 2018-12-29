import os

import argon2
import time

from bean.bean import get_db
from bean.session import new_session
from bean.usergroup import UserGroup, new_usergroup


def usergroup_by_name(name):
    cursor = get_db()

    row = cursor.execute("SELECT * FROM usergroup WHERE name = ?", [name]).fetchone()

    if row is None:
        return None

    cursor.commit()

    return UserGroup(row["id"])


def usergroup_by_auth_token(auth_token):
    cursor = get_db()

    try:
        row = cursor.execute("SELECT * FROM session WHERE auth_token = ?", [auth_token]).fetchone()

    except:
        return None

    return UserGroup(row["usergroup_id"])


def update_password(usergroup, password):

    password_salt = os.urandom(512)
    password_hashed = argon2.argon2_hash(password, password_salt)
    del password

    usergroup.password_salt = password_salt
    usergroup.password_hash = password_hashed


def register_usergroup(name, password_plain):
    password_salt = os.urandom(512)
    password_hashed = argon2.argon2_hash(password_plain, password_salt)
    del password_plain

    if usergroup_by_name(name) is not None:
        raise Exception("user already exists")

    return new_usergroup(name, password_salt, password_hashed)


def authorize(name, password_plain):
    usergroup = usergroup_by_name(name)

    if usergroup is None:
        raise Exception("user doesn't exist")

    password_hashed = argon2.argon2_hash(password_plain, usergroup.password_salt)
    del password_plain

    if password_hashed != usergroup.password_hash:
        raise Exception("password incorrect")

    auth_token = os.urandom(32).hex()
    session = new_session(usergroup.id, auth_token, int(time.time()))

    return auth_token


def activity(auth_token: str):
    cursor = get_db()

    try:
        cursor.execute("UPDATE session SET last_active = ? WHERE auth_token = ?", [int(time.time()), auth_token])
        cursor.commit()

    except:
        pass


def revoke_session(auth_token: str):
    cursor = get_db()

    try:
        cursor.execute("DELETE FROM session WHERE auth_token = ?", [auth_token])
        cursor.commit()

    except:
        pass


def cleanup_old_sessions():
    cursor = get_db()
    rows = cursor.execute("SELECT * FROM session")

    t0 = int(time.time())

    for row in rows:
        if t0 - row["last_active"] > 3 * 1440:
            try:
                cursor.execute("DELETE FROM session WHERE id = ?", [row["id"]])
            except:
                pass

    cursor.commit()


def is_authorized(auth_token: str):
    cursor = get_db()
    cleanup_old_sessions()

    res = cursor.execute("SELECT * FROM session WHERE auth_token = ?", [auth_token]).fetchone()

    return res is not None
