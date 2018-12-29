import csv


class Databatch(object):

    def __init__(self, path, encoding="utf-8-sig"):

        self.__entries = dict({})
        self.__row_count = 0

        with open(path, 'r+', encoding=encoding) as f:  # sometimes a leading blank line is injected
            lines = f.readlines()
            stripped_lines = []
            body = False

            for l in lines:  # only keep lines after (and including) first non blank line
                if body: stripped_lines.append(l)
                elif len(l.replace("\n", "")) > 0:
                    body = True
                    stripped_lines.append(l)

            f.seek(0)
            f.truncate(0)
            f.writelines(stripped_lines)


        with open(path, encoding=encoding) as f:
            reader = csv.reader(f)

            first_flag = True
            col_order = []

            for row in reader:

                if first_flag:
                    for col_name in row:
                        self.__entries[col_name] = []
                        col_order.append(col_name)

                    first_flag = False

                else:
                    for col_idx in range(len(col_order)):
                        col_name = col_order[col_idx]
                        self.__entries[col_name].append(row[col_idx])

                    self.__row_count += 1

    def get(self, col_name, index):
        return self.__entries[col_name][index]

    @property
    def row_count(self):
        return self.__row_count