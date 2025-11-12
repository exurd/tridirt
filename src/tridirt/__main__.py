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

TRID_COMMAND = [sys.executable, f"{INSTALL_DIR}/trid.py"]

DT_NOW = datetime.now()
DT_FORMAT = "%m-%d-%Y %H:%M:%S"


# create the install directory
if not os.path.exists(INSTALL_DIR):
    os.makedirs(INSTALL_DIR)


# init datetime variables
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


def get_trid():
    """Downloads trid from the url."""
    filename = URL_TRID_PROGRAM.rsplit('/', maxsplit=1)[-1]
    filepath = f"{INSTALL_DIR}/{filename}"

    # https://stackoverflow.com/a/37573701
    # Streaming, so we can iterate over the response.
    response = requests.get(URL_TRID_PROGRAM, stream=True, timeout=10)
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


def update_trid():
    """Checks for TrID program updates"""
    # check if it's been a few days since an update
    if (DT_NOW - timedelta(7)) > DT_TRID_LASTUPDATED:
        # send HEAD request for when the url was last modified
        request_trid_program = requests.head(url=URL_TRID_PROGRAM, timeout=10)
        if request_trid_program.ok:
            headers = request_trid_program.headers
            # https://stackoverflow.com/a/71637523
            dt_trid_update = datetime.strptime(headers["last-modified"], "%a, %d %b %Y %H:%M:%S %Z")
            # check date
            if dt_trid_update > DT_TRID_LASTUPDATED:
                print("Updating TrID...")
                get_trid()
                # write current date to last updated
                with open(FILE_TRID_LASTUPDATED, "w", encoding="utf-8") as f:
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


def main():
    """Main function for tridirt"""
    # TRID PROGRAM
    update_trid()

    # TRID DEFS
    update_trid_defs()

    # check to run trid with arguments that the user has given
    # remove first argument as it's the command name
    sys.argv.pop(0)
    if sys.argv:
        TRID_COMMAND.extend(sys.argv)
    # run!
    subprocess.call(TRID_COMMAND)
