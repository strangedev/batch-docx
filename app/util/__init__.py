import datetime
import os
from enum import Enum


def today():
    return datetime.datetime.now().date().isoformat()


def generate_outfile_path(phone_number):

    if not os.path.exists("/app/out"):
        os.mkdir("/app/out")

    phone_number = phone_number.replace("/", "-")
    outfile_path = os.path.join("/app/out", today())

    if not os.path.exists(outfile_path):
        os.mkdir(outfile_path)

    outfile_path = os.path.join(outfile_path, "{}.docx".format(phone_number))
    try_count = 0
    while True:
        if os.path.exists(outfile_path):
            outfile_path = os.path.join("/app/out", today(), phone_number + "_({}).docx".format(try_count))
            try_count += 1
        else:
            break

    return outfile_path


def generate_temp_filepath():
    path = "/tmp"
    filename = os.urandom(20).hex()
    ret = os.path.join(path, filename)

    while os.path.exists(ret):
        filename = os.urandom(20).hex()
        ret = os.path.join(path, filename)

    return ret

