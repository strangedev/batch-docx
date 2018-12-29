from typing import Any, Dict

import sqlite3

from flask import g


def get_db():

    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect("/app/database/serien.db")

    db.row_factory = sqlite3.Row

    return db


class Bean(object):

    bean_name = ""
    bean_description = {}

    def __init__(self, id: int):

        self.__id = id

    @property
    def id(self):
        return self.__id

    def _getMemberFromDb(self, member: str):

        result = get_db().execute(
            "SELECT * FROM {} WHERE id = (?)".format(self.__class__.bean_name),
            [self.__id]
        ).fetchone() # FIXME

        # noinspection PyTypeChecker
        return result[member]

    def _setMemberInDb(self, member: str, value: Any):

        cursor = get_db()

        cursor.execute(
            "UPDATE {} SET {} = (?) WHERE id = (?)".format(self.__class__.bean_name, member),
            [value, self.__id]
        )

        cursor.commit()


class BeanTableCreator(object):

    def __init__(self, bean_type):
        self.__bean_name = bean_type.bean_name
        self.__bean_description = bean_type.bean_description

    def register(self):
        cursor = get_db()

        sql_string = "CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY".format(self.__bean_name)

        for member_name, member_type in self.__bean_description.items():
            sql_string += ", {} {}".format(member_name, member_type)

        sql_string += ")"

        #print(sql_string)
        cursor.execute(sql_string)
        cursor.commit()


class BeanRelationCreator(object):

    def __init__(self, bean_type, another_bean_type):
        self.__bean_name = bean_type.bean_name
        self.__another_bean_name = another_bean_type.bean_name
        self.__table_name = self.__bean_name + "_" + self.__another_bean_name

    @property
    def table_name(self):
        return self.__table_name

    def register(self):
        cursor = get_db()

        # noinspection SqlNoDataSourceInspection
        sql_string = "CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY, {}_id INTEGER, {}_id INTEGER)".format(
            self.__table_name,
            self.__bean_name,
            self.__another_bean_name
        )

        #print(sql_string)
        cursor.execute(sql_string)
        cursor.commit()


class BeanCreator(object):

    def __init__(self, bean_type):

        self.__bean_type = bean_type
        self.__bean_name = bean_type.bean_name
        self.__bean_description = bean_type.bean_description

    def create(self, **kwargs):

        for key in kwargs.keys():
            if key not in self.__bean_description.keys():
                del kwargs[key]

        sql_string = "INSERT INTO {} (".format(self.__bean_name)

        first_flag = True

        for key in kwargs.keys():

            if not first_flag:
                sql_string += ", "

            else:
                first_flag = False

            sql_string += key

        sql_string += ") VALUES ("

        first_flag = True
        args = []

        for key in kwargs.keys():

            if not first_flag:
                sql_string += ", "

            else:
                first_flag = False

            sql_string += "?"
            args.append(kwargs[key])

        sql_string += ")"

        #print(sql_string)

        cursor = get_db().cursor()
        cursor.execute(sql_string, args)

        return self.__bean_type(cursor.lastrowid)
