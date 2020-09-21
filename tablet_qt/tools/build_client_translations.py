#!/usr/bin/env python

"""
tools/build_server_translations.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

**Make translation files for the CamCOPS C++ client, via Qt Linguist.**

For developer use only.

"""

import argparse
import logging
import os
from os.path import abspath, dirname, join
import shutil
from typing import Iterable, List

from cardinal_pythonlib.argparse_func import (
    RawDescriptionArgumentDefaultsHelpFormatter,
)
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from cardinal_pythonlib.subproc import check_call_verbose

log = BraceStyleAdapter(logging.getLogger(__name__))

CURRENT_DIR = dirname(abspath(__file__))  # camcops/tablet_qt/tools
TABLET_QT_DIR = abspath(join(CURRENT_DIR, os.pardir))  # camcops/tablet_qt
CAMCOPS_PRO_FILE = join(TABLET_QT_DIR, "camcops.pro")
TRANSLATIONS_DIR = join(TABLET_QT_DIR, "translations")  # .ts and .qm live here

ENVVAR_LCONVERT = "LCONVERT"
ENVVAR_LRELEASE = "LRELEASE"
ENVVAR_LUPDATE = "LUPDATE"

EXT_PO = ".po"
EXT_TS = ".ts"

OP_PO_TO_TS = "po2ts"
OP_SRC_TO_TS = "update"
OP_TS_TO_QM = "release"
OP_TS_TO_PO = "ts2po"
OP_ALL = "all"
ALL_OPERATIONS = [OP_PO_TO_TS, OP_SRC_TO_TS, OP_TS_TO_PO, OP_TS_TO_QM, OP_ALL]


# =============================================================================
# Support functions
# =============================================================================

def run(cmdargs: List[str]) -> None:
    """
    Runs a sub-command.

    Raises:
        :exc:CalledProcessError on failure

    Note that it is *critical* to abort on error; otherwise, for example, a
    process breaks the .pot file, and then this script chugs on and uses the
    broken .po file to break (for example) your Danish .po file.
    """
    check_call_verbose(cmdargs)


def change_extension(filename: str, new_ext: str) -> str:
    """
    Returns the same filename but with a different extension.
    The extension SHOULD START WITH A DOT.
    """
    return os.path.splitext(filename)[0] + new_ext


def first_file_newer_than_second(first: str, second: str) -> bool:
    """
    Compare file modification timestamps as the function name suggests.
    """
    first_time = os.path.getmtime(first)
    second_time = os.path.getmtime(second)
    return first_time > second_time


def convert_language_file_if_source_newer(source_filename: str,
                                          dest_filename: str,
                                          lconvert: str) -> None:
    """
    Converts a .po file to a .ts file (or vice versa), if either (a) the
    destination doesn't exist, or (b) the source is newer.
    """
    if (not os.path.exists(dest_filename) or
            first_file_newer_than_second(source_filename, dest_filename)):
        log.info(f"Converting {source_filename} -> {dest_filename}")
        run([
            lconvert,
            "-locations", "relative",
            source_filename,
            "-o", dest_filename
        ])


def gen_files_with_ext(directory: str, ext: str) -> Iterable[str]:
    """
    Yields all filenames within 'directory' that end in the specified
    extension. This function does NOT traverse subdirectories.

    See e.g.
    https://stackoverflow.com/questions/3964681/find-all-files-in-a-directory-with-extension-txt-in-python
    """  # noqa
    for filename in os.listdir(directory):
        if filename.endswith(ext):
            yield filename


# =============================================================================
# Command-line entry point
# =============================================================================

def main() -> None:
    """
    Create translation files for the CamCOPS client.
    """  # noqa
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        description=f"""
Create translation files for CamCOPS client.

Operations:

    {OP_PO_TO_TS}
        Special.
        Converts all.po files to .ts files in the translations directory, if
        and only if the .ts file is newer than the .po file.

    {OP_SRC_TO_TS}
        Updates all .ts files (which are XML, one per language) from the .pro
        file and thence the C++ source code.

    [At this stage, you could edit the .ts files with Qt Linguist. If you
    can't find it, use Qt Creator and look within your project in "Other files"
    / "Translations", right-click a .ts file, and then "Open With" / "Qt
    Linguist".]

    {OP_TS_TO_PO}
        Special.
        Converts all Qt .ts files to .po files in the translations directory,
        if and only if the .ts file is newer than the .po file.

    {OP_TS_TO_QM}
        Updates all .qm files (which are binary) from the corresponding .ts
        files (discovered via the .pro file).

    {OP_ALL}
        Executes all other operations in sequence.""",
        formatter_class=RawDescriptionArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "operation", choices=ALL_OPERATIONS,
        metavar="operation",
        help=f"Operation to perform; possibilities are {ALL_OPERATIONS!r}"
    )
    parser.add_argument(
        "--lconvert", action="store_true",
        help=f"Path to 'lconvert' tool (part of Qt Linguist). "
             f"Default is taken from {ENVVAR_LCONVERT} environment variable "
             f"or 'which lconvert'.",
        default=os.environ.get(ENVVAR_LCONVERT) or shutil.which("lconvert")
    )
    parser.add_argument(
        "--lrelease", action="store_true",
        help=f"Path to 'lrelease' tool (part of Qt Linguist). "
             f"Default is taken from {ENVVAR_LRELEASE} environment variable "
             f"or 'which lrelease'.",
        default=os.environ.get(ENVVAR_LRELEASE) or shutil.which("lrelease")
    )
    parser.add_argument(
        "--lupdate", action="store_true",
        help=f"Path to 'lupdate' tool (part of Qt Linguist). "
             f"Default is taken from {ENVVAR_LUPDATE} environment variable "
             f"or 'which lupdate'.",
        default=os.environ.get(ENVVAR_LUPDATE) or shutil.which("lupdate")
    )
    parser.add_argument(
        "--trim", action="store_true",
        help="Remove redundant strings."
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Be verbose"
    )
    args = parser.parse_args()
    main_only_quicksetup_rootlogger(
        level=logging.DEBUG if args.verbose else logging.INFO)
    op = args.operation  # type: str

    if op in [OP_PO_TO_TS, OP_ALL]:
        log.info(
            f"Copying all {EXT_PO} files to corresponding {EXT_TS} files if "
            f"the {EXT_PO} file is newer (or the {EXT_TS} file doesn't "
            f"exist).")
        for source_filename in gen_files_with_ext(TRANSLATIONS_DIR, EXT_PO):
            dest_filename = change_extension(source_filename, EXT_TS)
            convert_language_file_if_source_newer(
                source_filename=source_filename,
                dest_filename=dest_filename,
                lconvert=args.lconvert
            )

    if op in [OP_SRC_TO_TS, OP_ALL]:
        assert args.lupdate, "Missing lupdate"
        log.info(f"Using Qt Linguist 'lupdate' to update .ts files "
                 f"from {CAMCOPS_PRO_FILE}")
        options = ["-no-obsolete"] if args.trim else []
        cmdargs = [args.lupdate] + options + [CAMCOPS_PRO_FILE]
        run(cmdargs)

    if op in [OP_TS_TO_PO, OP_ALL]:
        log.info(
            f"Copying all {EXT_TS} files to corresponding {EXT_PO} files if "
            f"the {EXT_PO} file is newer (or the {EXT_PO} file doesn't "
            f"exist).")
        for source_filename in gen_files_with_ext(TRANSLATIONS_DIR, EXT_TS):
            dest_filename = change_extension(source_filename, EXT_PO)
            convert_language_file_if_source_newer(
                source_filename=source_filename,
                dest_filename=dest_filename,
                lconvert=args.lconvert
            )

    if op in [OP_TS_TO_QM, OP_ALL]:
        assert args.lrelease, "Missing lrelease"
        log.info(f"Using Qt Linguist 'lupdate' to update .ts files "
                 f"from {CAMCOPS_PRO_FILE}")
        cmdargs = [args.lrelease, CAMCOPS_PRO_FILE]
        run(cmdargs)


if __name__ == "__main__":
    main()
