#!/usr/bin/env bash

# Run from .github/workflows/docs.yml
# Rebuild Sphinx docs from scratch and check generated files match those checked
# in

set -eux -o pipefail

sudo apt-get install texlive-latex-extra dvipng
python -m venv "${HOME}/venv"
source "${HOME}/venv/bin/activate"
python -VV
python -m site
python -m pip install -U pip
# Until numpy is fixed
# https://github.com/numpy/numpy/issues/22623
python -m pip install setuptools<60
echo installing pip packages
cd "${GITHUB_WORKSPACE}/server"
python -m pip install -e .
python -m pip install mysqlclient
export CAMCOPS_CONFIG_FILE=${HOME}/camcops.cfg
camcops_server demo_camcops_config > $CAMCOPS_CONFIG_FILE
########################################################################################
cd "${GITHUB_WORKSPACE}/docs"
echo Creating autodocs
python ./create_all_autodocs.py --make --destroy_first
cd "${GITHUB_WORKSPACE}"
echo Checking if files generated by create_all_autodocs need to be checked in
git diff
git update-index --refresh
git diff-index --quiet HEAD --
test -z "$(git ls-files --exclude-standard --others)"
cd docs
echo Rebuilding docs
python ./rebuild_docs.py --skip_client_help --warnings_as_errors
echo Checking if files generated by rebuild_docs need to be checked in
git diff
git update-index --refresh
git diff-index --quiet HEAD --
test -z "$(git ls-files --exclude-standard --others)"
