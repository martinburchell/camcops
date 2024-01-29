#!/bin/bash
set -euxo pipefail
export CAMCOPS_QT6_BASE_DIR=${RUNNER_WORKSPACE}
cd ${CAMCOPS_QT6_BASE_DIR}
mkdir -p eigen
cd eigen
EIGEN_VERSION_FILE=${GITHUB_WORKSPACE}/tablet_qt/eigen_version.txt
EIGEN_VERSION=$(<$EIGEN_VERSION_FILE)
wget --retry-on-http-error=429 --waitretry=300 --tries=20 https://gitlab.com/libeigen/eigen/-/archive/${EIGEN_VERSION}/eigen-${EIGEN_VERSION}.tar.gz
tar xzf eigen-${EIGEN_VERSION}.tar.gz
cd ${GITHUB_WORKSPACE}
mkdir build-qt6-tests
cd build-qt6-tests
qmake ../tablet_qt/tests
make
export QT_DEBUG_PLUGINS=1

find . -path '*/bin/*' -type f -exec {} \;
