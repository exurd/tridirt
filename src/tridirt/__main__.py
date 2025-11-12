import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from zipfile import ZipFile

from tqdm import tqdm
import requests


HOME_DIR = Path.home()
INSTALL_DIR = f"{HOME_DIR}/.trid"

URL_TRID_PROGRAM = "https://mark0.net/download/trid.zip"
URL_TRID_DEFS = "https://mark0.net/download/triddefs.zip"
URL_TRIDSCAN = "https://mark0.net/download/tridscan.zip"
URL_TRIDDEFSPACK = "https://mark0.net/download/triddefspack.zip"

COMMAND_TRID = [sys.executable, f"{INSTALL_DIR}/trid.py"]
COMMAND_TRIDSCAN = [sys.executable, f"{INSTALL_DIR}/tridscan.py"]
COMMAND_TRIDDEFSPACK = [sys.executable, f"{INSTALL_DIR}/triddefspack.py"]

DT_NOW = datetime.now()
DT_FORMAT = "%m-%d-%Y %H:%M:%S"


# create the install directory
if not os.path.exists(INSTALL_DIR):
    os.makedirs(INSTALL_DIR)


def get_datetime(filename):
    """Gets the datetime from a filename."""
    dt = datetime(1, 1, 1)  # default to use if it fails
    if os.path.exists(filename) and os.path.getsize(filename) != 0:
        with open(filename, "r", encoding="utf-8") as f:
            f.seek(0)
            dt = datetime.strptime(f.read(), DT_FORMAT)
    return dt


FILE_TRID_LASTUPDATED = f"{INSTALL_DIR}/TRID_LU"
DT_TRID_LASTUPDATED = get_datetime(FILE_TRID_LASTUPDATED)

FILE_TRIDDEFS_LASTUPDATED = f"{INSTALL_DIR}/TRID_DEFS_LU"
DT_TRIDDEFS_LASTUPDATED = get_datetime(FILE_TRIDDEFS_LASTUPDATED)

FILE_TRIDSCAN_LASTUPDATED = f"{INSTALL_DIR}/TRIDSCAN_LU"
DT_TRIDSCAN_LASTUPDATED = get_datetime(FILE_TRIDSCAN_LASTUPDATED)

FILE_TRIDDEFSPACK_LASTUPDATED = f"{INSTALL_DIR}/TRIDDEFSPACK_LU"
DT_TRIDDEFSPACK_LASTUPDATED = get_datetime(FILE_TRIDDEFSPACK_LASTUPDATED)


# https://stackoverflow.com/a/3041990
def query(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"invalid default answer: '{default}'")

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def get_program(url: str):
    """Downloads the program from the url and unextracts it."""
    filename = url.rsplit('/', maxsplit=1)[-1]
    filepath = f"{INSTALL_DIR}/{filename}"

    # https://stackoverflow.com/a/37573701
    # Streaming, so we can iterate over the response.
    response = requests.get(url, stream=True, timeout=10)
    # Sizes in bytes.
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024
    with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
        with open(filepath, "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)

    if total_size != 0 and progress_bar.n != total_size:
        raise RuntimeError("Could not download file")

    # now extract the zip file
    with ZipFile(filepath, "r") as zf:
        zf.extractall(INSTALL_DIR)


def update_program(url, dt_lastupdated, file_lastupdated):
    """Checks for program updates"""
    # check if it's been a few days since an update
    if (DT_NOW - timedelta(7)) > dt_lastupdated:
        # send HEAD request for when the url was last modified
        request_program = requests.head(url, timeout=10)
        if request_program.ok:
            headers = request_program.headers
            # https://stackoverflow.com/a/71637523
            dt_lastmodified = datetime.strptime(headers["last-modified"], "%a, %d %b %Y %H:%M:%S %Z")
            # check date
            if dt_lastmodified > dt_lastupdated:
                print("New version is available!")
                print(f"Downloading {url}...")
                get_program(url)
                # write current date to last updated
                with open(file_lastupdated, "w", encoding="utf-8") as f:
                    f.write(DT_NOW.strftime(DT_FORMAT))


def update_trid_defs():
    """Checks for TrID definition updates"""
    # check if defs are installed
    if not os.path.exists(f"{INSTALL_DIR}/triddefs.trd"):
        # if not, ask trid to install them
        subprocess.call([sys.executable, f"{INSTALL_DIR}/trid.py", "--update"])
    else:
        # check if it's been a few days since an update
        if (DT_NOW - timedelta(2)) > DT_TRIDDEFS_LASTUPDATED:
            # send HEAD request for when the url was last modified
            request_trid_defs = requests.head(url=URL_TRID_DEFS, timeout=10)
            if request_trid_defs.ok:
                headers = request_trid_defs.headers
                last_mod = headers["last-modified"]
                # https://stackoverflow.com/a/71637523
                dt_triddefs_update = datetime.strptime(last_mod, "%a, %d %b %Y %H:%M:%S %Z")
                # check date
                if dt_triddefs_update > DT_TRIDDEFS_LASTUPDATED:
                    subprocess.call([sys.executable, f"{INSTALL_DIR}/trid.py", "--update"])
                    # write current date to last updated
                    with open(FILE_TRIDDEFS_LASTUPDATED, "w", encoding="utf-8") as f:
                        f.write(DT_NOW.strftime(DT_FORMAT))


def trid_main():
    """Console script function for trid"""
    # check if trid is not installed
    if not os.path.exists(COMMAND_TRID[1]):
        if not query("Not installed. Do you want to install TrID?"):
            sys.exit(1)

    # TRID PROGRAM
    update_program(URL_TRID_PROGRAM,
                   DT_TRID_LASTUPDATED,
                   FILE_TRID_LASTUPDATED)

    # TRID DEFS
    update_trid_defs()

    # RUN TRID
    # remove first argument as it's the command name
    sys.argv.pop(0)
    if sys.argv:
        COMMAND_TRID.extend(sys.argv)
    # run!
    subprocess.call(COMMAND_TRID)


def tridscan_main():
    """Console script function for tridscan"""
    # check if tridscan is not installed
    if not os.path.exists(COMMAND_TRIDSCAN[1]):
        if not query("Not installed. Do you want to install TrIDScan?"):
            sys.exit(1)

    # TRIDSCAN
    update_program(URL_TRIDSCAN,
                   DT_TRIDSCAN_LASTUPDATED,
                   FILE_TRIDSCAN_LASTUPDATED)

    # RUN TRIDSCAN
    # remove first argument as it's the command name
    sys.argv.pop(0)
    if sys.argv:
        COMMAND_TRIDSCAN.extend(sys.argv)
    # run!
    subprocess.call(COMMAND_TRIDSCAN)


def triddefspack_main():
    """Console script function for triddefspack"""
    # check if triddefspack is installed
    if not os.path.exists(COMMAND_TRIDDEFSPACK[1]):
        if not query("Not installed. Do you want to install TrIDDefsPack?"):
            sys.exit(1)

    # TRIDDEFSPACK
    update_program(URL_TRIDDEFSPACK,
                   DT_TRIDDEFSPACK_LASTUPDATED,
                   FILE_TRIDDEFSPACK_LASTUPDATED)

    # RUN TRIDDEFSPACK
    # remove first argument as it's the command name
    sys.argv.pop(0)
    if sys.argv:
        COMMAND_TRIDSCAN.extend(sys.argv)
    # run!
    subprocess.call(COMMAND_TRIDDEFSPACK)
