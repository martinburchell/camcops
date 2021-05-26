#!/usr/bin/env python

"""
tools/reformat_source.py

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**Clean up source code.**

"""

import argparse
import logging
from os import pardir
from os.path import abspath, dirname, join

from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from cardinal_pythonlib.source_reformatting import reformat_python_docstrings

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Directories
# =============================================================================

THIS_DIR = abspath(dirname(__file__))  # .../camcops/server/tools
CAMCOPS_ROOT_DIR = abspath(join(THIS_DIR, pardir, pardir))  # .../camcops
SERVER_ROOT_DIR = join(CAMCOPS_ROOT_DIR, 'server')  # .../camcops/server
TABLET_ROOT_DIR = join(CAMCOPS_ROOT_DIR, 'tablet_qt')  # .../camcops/tablet_qt


# =============================================================================
# Content
# =============================================================================

CORRECT_COPYRIGHT_LINES = """
===============================================================================

    Copyright (C) 2012-2020 University of Cambridge.
    Created by Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================
""".strip().splitlines()


# =============================================================================
# Top-level functions
# =============================================================================

def main() -> None:
    """
    Command-line entry point. See command-line help.
    """
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Reformat source files")
    parser.add_argument(
        "--rewrite", action="store_true",
        help="Rewrite the files")
    parser.add_argument(
        "--show", action="store_true",
        help="Show the files to stdout")
    parser.add_argument(
        "--process_only_filenum", type=int,
        help="Only process this file number (1-based index) in each "
             "directory; for debugging only")

    args = parser.parse_args()

    rewrite = args.rewrite
    show_only = args.show
    process_only_filenum = args.process_only_filenum

    if not rewrite and not show_only:
        log.info("Not rewriting and not showing; will just catalogue files "
                 "and report things it's changing")

    reformat_python_docstrings(
        top_dirs=[SERVER_ROOT_DIR, TABLET_ROOT_DIR],
        show_only=show_only,
        rewrite=rewrite,
        process_only_filenum=process_only_filenum,
        correct_copyright_lines=CORRECT_COPYRIGHT_LINES
    )


if __name__ == "__main__":
    main()
