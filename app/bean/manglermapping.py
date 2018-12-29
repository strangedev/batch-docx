from flask import json

import util
from bean import bean


def new_manglermapping(template_id, name):
    cur = bean.get_db().cursor()
    cur.execute("INSERT INTO manglermapping "
                "(name, template_id, date_added, date_last_used, mappings_json) "
                "VALUES (?, ?, ?, ?, ?)",
                [name, template_id, util.today(), "", json.dumps(dict({}))])

    return ManglerMapping(cur.lastrowid)


def delete_manglermapping(mapping):
    cur = bean.get_db().cursor()
    cur.execute("DELETE FROM manglermapping WHERE id = ?", [mapping.id])


def mappings_by_template(template_id):
    cur = bean.get_db()
    res = cur.execute("SELECT manglermapping.id AS m_id "
                      "FROM manglermapping "
                      "WHERE template_id = ?", [template_id])

    return [ManglerMapping(r["m_id"]) for r in res]


class ManglerMapping(bean.Bean):
    bean_name = "manglermapping"
    bean_description = {
        "name": "TEXT",
        "template_id": "INTEGER",
        "date_added": "TEXT",
        "date_last_used": "TEXT",
        "mappings_json": "TEXT",
        "replacements_json": "TEXT",
    }

    @property
    def name(self):
        return super()._getMemberFromDb("name")

    @name.setter
    def name(self, value):
        super()._setMemberInDb("name", value)

    @property
    def template_id(self):
        return super()._getMemberFromDb("template_id")

    @template_id.setter
    def template_id(self, value):
        super()._setMemberInDb("template_id", value)

    @property
    def date_added(self):
        return super()._getMemberFromDb("date_added")

    @date_added.setter
    def date_added(self, value):
        super()._setMemberInDb("date_added", value)

    @property
    def date_last_used(self):
        return super()._getMemberFromDb("date_last_used")

    @date_last_used.setter
    def date_last_used(self, value):
        super()._setMemberInDb("date_last_used", value)

    @property
    def mappings_json(self):
        return super()._getMemberFromDb("mappings_json")

    @mappings_json.setter
    def mappings_json(self, value):
        super()._setMemberInDb("mappings_json", value)

    @property
    def replacements_json(self):
        return super()._getMemberFromDb("replacements_json")

    @replacements_json.setter
    def replacements_json(self, value):
        super()._setMemberInDb("replacements_json", value)

    def find_mapping(self, value):
        return json.loads(self.mappings_json)[value]

    def set_mapping(self, key: str, value: str):

        if len(self.mappings_json) == 0:
            mappings = {}

        else:
            mappings = json.loads(self.mappings_json)

        mappings[key] = value

        self.mappings_json = json.dumps(mappings)

    def find_replacement(self, value):
        return json.loads(self.replacements_json)[value]

    def set_replacement(self, key: str, value: str):

        if len(self.replacements_json) == 0:
            replacements = {}

        else:
            replacements = json.loads(self.replacements_json)

        replacements[key] = value

        self.replacements_json = json.dumps(replacements)

    def replace_mappings(self, mappings):
        self.mappings_json = json.dumps(mappings)

    def replace_replacements(self, replacements):
        self.replacements_json = json.dumps(replacements)

    def merge_from(self, mapping, keep_own_values=True, exclusive_merge=False):

        if type(mapping) is dict:
            other_mappings = mapping
            other_replacements = dict()

        else:
            other_mappings = json.loads(mapping.mappings_json)
            other_replacements = json.loads(mapping.replacements_json)

        own_mappings = json.loads(self.mappings_json)
        own_replacements = json.loads(self.replacements_json)

        for k, v in other_mappings.items():

            if k not in own_mappings.keys():
                self.set_mapping(k, v)

            elif not keep_own_values:
                self.set_mapping(k, v)

        for k, v in other_replacements.items():

            if k not in own_replacements.keys():
                self.set_replacement(k, v)

            elif not keep_own_values:
                self.set_replacement(k, v)

        if not exclusive_merge:
            return

        own_mappings = json.loads(self.mappings_json)

        for k in list(own_mappings.keys()):
            if k not in other_mappings.keys():
                del own_mappings[k]

        self.replace_mappings(own_mappings)