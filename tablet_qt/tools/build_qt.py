#!/usr/bin/env python3.5

"""
When is it NECESSARY to compile OpenSSL from source?
    - OpenSSL for Android
      http://doc.qt.io/qt-5/opensslsupport.html
      ... so: necessary.

When is it NECESSARY to compile Qt from source?
    - Static linking of OpenSSL (non-critical)
    - SQLite support (critical)
      http://doc.qt.io/qt-5/sql-driver.html
      ... so: necessary.

COMPILING OPENSSL:
    ...

OTHER NOTES:
# configure: http://doc.qt.io/qt-5/configure-options.html
# sqlite: http://doc.qt.io/qt-5/sql-driver.html
# build for Android: http://wiki.qt.io/Qt5ForAndroidBuilding
# multi-core builds: http://stackoverflow.com/questions/9420825/how-to-compile-on-multiple-cores-using-mingw-inside-qtcreator  # noqa

UPON QT CONFIGURE FAILURE:

-   gstreamer (used for Unix audio etc.)
    gstreamer version 1.0 version (for Unix) requires:
        sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
    ... NB some things try to remove it, it seems! (Maybe autoremove?)

-   Qt configure can't find make or gmake in PATH...

    If they are in the PATH, then check permissions on
          qtbase/config.tests/unix/which.test
    ... if not executable, permissions have been altered wrongly.

-   NB actual configure scripts are:
        /home/rudolf/dev/qt_local_build/src/qt5/configure
        /home/rudolf/dev/qt_local_build/src/qt5/configure/qtbase/configure

-   "recipe for target 'sub-plugins-make_first' failed", or similar:

    If configure fails, try more or less verbose (--verbose 0, --verbose 2) and
    also try "--nparallel 1" so you can see which point is failing more
    clearly. This is IMPORTANT or other error messages incorrectly distract
    you.

"""


import argparse
from contextlib import contextmanager
import logging
import multiprocessing
import os
from os.path import abspath, expanduser, isdir, isfile, join, split
import platform
from pprint import pformat
import shlex
import shutil
import subprocess
import sys
import traceback
from typing import Dict, List, Tuple
import urllib.request

log = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

USE_MLPACK = False
USE_ARMADILLO = USE_MLPACK
USE_BOOST = USE_MLPACK

USE_EIGEN = True

USER_DIR = expanduser("~")
HEAD = "HEAD"  # git commit meaning "the most recent"

ENVVAR_QT_BASE = "CAMCOPS_QT_BASE_DIR"

# -----------------------------------------------------------------------------
# Downloading and versions
# -----------------------------------------------------------------------------

# Android
DEFAULT_ANDROID_API_NUM = 23
DEFAULT_ROOT_DIR = join(USER_DIR, "dev", "qt_local_build")
DEFAULT_ANDROID_SDK = join(USER_DIR, "dev", "android-sdk-linux")
DEFAULT_ANDROID_NDK = join(USER_DIR, "dev", "android-ndk-r11c")
DEFAULT_NDK_HOST = "linux-x86_64"
DEFAULT_TOOLCHAIN_VERSION = "4.9"

# Qt
DEFAULT_QT_SRC_DIRNAME = "qt5"
DEFAULT_QT_GIT_URL = "git://code.qt.io/qt/qt5.git"
DEFAULT_QT_GIT_BRANCH = "5.9"  # previously "5.7.0"
DEFAULT_QT_GIT_COMMIT = HEAD
DEFAULT_QT_USE_OPENSSL_STATICALLY = True
FIX_QT_5_7_0_ANDROID_MAKE_INSTALL_BUG = False  # was necessary for v5.7.0
ADD_SO_VERSION_OF_LIBQTFORANDROID = False

# OpenSSL
DEFAULT_OPENSSL_VERSION = "1.0.2h"
DEFAULT_OPENSSL_SRC_URL = (
    "https://www.openssl.org/source/openssl-{}.tar.gz".format(
        DEFAULT_OPENSSL_VERSION))
DEFAULT_OPENSSL_ANDROID_SCRIPT_URL = \
    "https://wiki.openssl.org/images/7/70/Setenv-android.sh"

# SQLCipher; https://www.zetetic.net/sqlcipher/open-source/
DEFAULT_SQLCIPHER_GIT_URL = "https://github.com/sqlcipher/sqlcipher.git"
DEFAULT_SQLCIPHER_GIT_COMMIT = HEAD
# note that there's another URL for the Android binary packages

# Boost
DEFAULT_BOOST_VERSION = "1.64.0"
DEFAULT_BOOST_SRC_URL = (
    "https://dl.bintray.com/boostorg/"
    "release/{vdot}/source/boost_{vund}.tar.gz".format(
        vdot=DEFAULT_BOOST_VERSION,
        vund=DEFAULT_BOOST_VERSION.replace(".", "_"),
    )
    # It looks like there's an extra ":" before the final "boost" in the
    # list at https://dl.bintray.com/boostorg/release/1.64.0/source/
    # but the URL only works if you remove it.
)

# Armadillo
DEFAULT_ARMA_VERSION = "7.950.0"
DEFAULT_ARMA_SRC_URL = (
    "http://sourceforge.net/projects/arma/files/"
    "armadillo-{}.tar.xz".format(
        DEFAULT_ARMA_VERSION))

# MLPACK; http://mlpack.org/
DEFAULT_MLPACK_GIT_URL = "https://github.com/mlpack/mlpack"
DEFAULT_MLPACK_GIT_COMMIT = HEAD

# Eigen
DEFAULT_EIGEN_VERSION = "3.3.3"

# -----------------------------------------------------------------------------
# Constants: building Qt
# -----------------------------------------------------------------------------
# TO MAKE MINOR CHANGES: delete ...installdir/bin/qmake, and rerun this script.
# (Can still take ages. Not sure it saves any time, in fact.)

QT_CONFIG_COMMON_ARGS = [
    # use "configure -help" to list all of them
    # http://doc.qt.io/qt-4.8/configure-options.html  # NB better docs than 5.7
    # http://doc.qt.io/qt-5.7/configure-options.html  # less helpful
    # http://doc.qt.io/qt-5.9/configure-options.html

    # -------------------------------------------------------------------------
    # Qt license, debug v. release,
    # -------------------------------------------------------------------------

    "-opensource", "-confirm-license",  # Choose our Qt edition.

    "-release",  # Make a release-mode library. (Default is release.)

    # "-debug-and-release",  # make a release library as well: MAC ONLY
    # ... debug was the default in 4.8, but not in 5.7
    # ... release is default in 5.7 (as per "configure -h")
    # ... check with "readelf --debug-dump=decodedline <LIBRARY.so>"
    # ... http://stackoverflow.com/questions/1999654

    # -------------------------------------------------------------------------
    # static v. shared
    # -------------------------------------------------------------------------
    # Now decided on a per-platform basis (2017-06-18)

    # -------------------------------------------------------------------------
    # Database support
    # -------------------------------------------------------------------------

    # v5.7.0 # "-qt-sql-sqlite",  # SQLite (v3) support built in to Qt
    "-sql-sqlite",  # v5.9: explicitly add SQLite support
    "-qt-sqlite",  # v5.9: "qt", rather than "system"

    "-no-sql-db2",  # disable other SQL drivers
    "-no-sql-ibase",
    "-no-sql-mysql",  # ... for future: maybe re-enable as a plugin
    "-no-sql-oci",
    "-no-sql-odbc",  # ... for future: maybe re-enable as a plugin
    "-no-sql-psql",  # ... for future: maybe re-enable as a plugin
    "-no-sql-sqlite2",  # this is an old SQLite version
    "-no-sql-tds",  # this one specifically was causing library problems

    # -------------------------------------------------------------------------
    # Libraries
    # -------------------------------------------------------------------------

    "-qt-doubleconversion",  # Use Qt version of double conversion library
    # NOT YET WORKING ("Qt no longer ships fonts") # "-qt-freetype",  # Qt, not system, version of Freetype  # noqa
    # NOT YET WORKING ("Qt no longer ships fonts") # "-qt-harfbuzz",  # Qt, not system, version of HarfBuzz-NG  # noqa
    "-qt-libjpeg",  # Qt, not host OS, version of JPEG library
    "-qt-libpng",  # Qt, not host OS, version of PNG library
    "-qt-zlib",  # Qt, not host OS, version of zlib

    # -------------------------------------------------------------------------
    # Compilation
    # -------------------------------------------------------------------------
    # Note: the default release build optimizes with -O2 -Os; there are
    # some 'configure' options to control this, but it's probably a good
    # default.

    "-no-warnings-are-errors",  # don't treat warnings as errors

    # -------------------------------------------------------------------------
    # Stuff to skip
    # -------------------------------------------------------------------------
    # CHANGE OF HEART: don't skip anything; it leads to trouble later!

    # not a valid "-nomake": # "-nomake", "docs",
    # not a valid "-nomake": # "-nomake", "demos",
    "-nomake", "examples",
    "-nomake", "tests",

    # "-skip", "qttranslations",

    # Don't need this on any platform, and unsupported on Android:
    "-skip", "qtserialport",

    # Except the webkit stuff, which ends up giving problems with Wayland-EGL:
    # "-skip", "qtwebkit",  # disabled 2017-10-22: "Project ERROR: -skip command line argument used with non-existent module 'qtwebkit'."  # noqa
    # "-skip", "qtwebkit-examples",  # disabled 2017-10-22: ditto
]

# -----------------------------------------------------------------------------
# Constants: building OpenSSL
# -----------------------------------------------------------------------------

OPENSSL_COMMON_OPTIONS = [
    "shared",  # make .so files (needed by Qt sometimes) as well as .a
    "no-ssl2",  # SSL-2 is broken
    "no-ssl3",  # SSL-3 is broken. Is an SSL-3 build required for TLS 1.2?
    # "no-comp",  # disable compression independent of zlib
]

# -----------------------------------------------------------------------------
# Constants: external tools
# -----------------------------------------------------------------------------

CMAKE = "cmake"
GOBJDUMP = "gobjdump"  # OS/X equivalent of readelf
MAKE = "make"
READELF = "readelf"  # read ELF-format library files
SED = "sed"  # stream editor
TAR = "tar"  # manipulate tar files
XCODE_SELECT = "xcode-select"  # OS/X tool to find paths for XCode

# -----------------------------------------------------------------------------
# Constants for building
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

LOG_FORMAT = '%(asctime)s.%(msecs)03d:%(levelname)s:%(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'


# =============================================================================
# Information about the target system
# =============================================================================

class Os(object):
    ANDROID = "android"
    LINUX = "linux"
    WINDOWS = "windows"
    OSX = "osx"
    IOS = "ios"


ALL_OSS = [getattr(Os, _) for _ in dir(Os) if not _.startswith("_")]


class Cpu(object):
    X86_32 = "x86"
    X86_64 = "x86_64"
    ARM_V5 = "armv5"  # 32-bit; https://en.wikipedia.org/wiki/ARM_architecture
    ARM_V7 = "armv7"  # 32-bit; https://en.wikipedia.org/wiki/ARM_architecture
    ARM_V8_64 = "armv8_64"


ALL_CPUS = [getattr(Cpu, _) for _ in dir(Cpu) if not _.startswith("_")]


class Platform(object):
    # noinspection PyShadowingNames
    def __init__(self, os: str, cpu: str) -> None:
        self.os = os
        self.cpu = cpu
        if os not in ALL_OSS:
            raise ValueError("Unknown target OS: {!r}".format(os))
        if cpu not in ALL_CPUS:
            raise ValueError("Unknown target CPU: {!r}".format(cpu))

        if os in [Os.LINUX, Os.OSX, Os.WINDOWS] and cpu != Cpu.X86_64:
            raise ValueError("Don't know how to build for CPU " + cpu +
                             " on system " + os)

    def __str__(self) -> str:
        return self.description

    @property
    def description(self) -> str:
        return "{}/{}".format(self.os, self.cpu)

    @property
    def dirpart(self) -> str:
        return "{}_{}".format(self.os, self.cpu)

    @staticmethod
    def shared_lib_suffix() -> str:
        # I think this depends on the host, not the target.
        if HOST_PLATFORM.os in [Os.OSX]:
            return ".dylib"
        else:
            return ".so"

    @property
    def linux(self) -> bool:
        return self.os == Os.LINUX

    @property
    def osx(self) -> bool:
        return self.os == Os.OSX

    @property
    def android(self) -> bool:
        return self.os == Os.ANDROID

    @property
    def ios(self) -> bool:
        return self.os == Os.IOS

    @property
    def mobile(self) -> bool:
        return self.os in [Os.ANDROID, Os.IOS]

    @property
    def desktop(self) -> bool:
        return not self.mobile

    @property
    def cpu_x86_family(self) -> bool:
        return self.cpu in [Cpu.X86_32, Cpu.X86_64]

    @property
    def cpu_arm_family(self) -> bool:
        return self.cpu in [Cpu.ARM_V5, Cpu.ARM_V7, Cpu.ARM_V8_64]

    @property
    def android_cpu(self) -> str:
        """
        CPU name for Android builds.
        """
        if not self.android:
            raise ValueError("Platform is not Android")
        if self.cpu == Cpu.X86_64:
            return "x86_64"
        elif self.cpu == Cpu.ARM_V7:
            return "arm"
        elif self.cpu == Cpu.ARM_V5:
            return "armv5"
        else:
            raise ValueError("Don't know how to build Android for CPU " +
                             self.cpu)

    @property
    def android_arch_short(self) -> str:
        return self.android_cpu

    @property
    def android_arch_full(self) -> str:
        # e.g. arch-x86
        return "arch-{}".format(self.android_arch_short)

    def ensure_elf_reader(self) -> None:
        """Only to be called for the host platform."""
        if self.linux:
            require(READELF)
        elif self.osx:
            require(GOBJDUMP)
        else:
            raise ValueError("Don't know ELF reader for {}".format(
                HOST_PLATFORM))

    def verify_elf(self, filename: str) -> None:
        """
        Check an ELF file matches our architecture.
        """
        log.info("Verifying type of ELF file: {!r}".format(filename))
        if HOST_PLATFORM.linux:
            elf_arm_tag = "Tag_ARM_ISA_use: Yes"
            elfcmd = [READELF, "-A", filename]
            log.info("Checking ELF information for " + repr(filename))
            elfresult, _ = run(elfcmd, get_output=True)
            if self.cpu_arm_family:
                if elf_arm_tag not in elfresult:
                    log.critical(elfresult)
                    raise ValueError(
                        "File {} was not build for ARM".format(filename))
        elif HOST_PLATFORM.osx:
            # https://lowlevelbits.org/parsing-mach-o-files/
            # https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
            # gobjdump --help
            dumpcmd = [GOBJDUMP, "-f", filename]
            dumpresult, _ = run(dumpcmd, get_output=True)
            arm64tag = "file format mach-o-arm64"
            if self.cpu == Cpu.ARM_V8_64:
                if arm64tag not in dumpresult:
                    log.critical(dumpresult)
                    raise ValueError(
                        "File {} was not build for ARM64".format(filename))
        else:
            raise ValueError("Don't know how to verify ELF for {}".format(
                HOST_PLATFORM))
        log.info("ELF file is good: {!r}".format(filename))

    @property
    def ios_platform_name(self) -> str:
        if not self.ios:
            raise ValueError("ios_platform_name requested but not using iOS")
        if self.cpu_x86_family:
            return "iPhoneSimulator"
        elif self.cpu_arm_family:
            return "iPhoneOS"
        else:
            raise ValueError("Unknown combination for ios_platform_name")

    @property
    def ios_arch(self) -> str:
        if self.cpu == Cpu.X86_64:
            return "x86_64"
        elif self.cpu == Cpu.X86_32:
            return "i386"
        elif self.cpu == Cpu.ARM_V7:
            return "armv7"
        elif self.cpu == Cpu.ARM_V8_64:
            return "arm64"
        else:
            raise ValueError("Unknown architecture for iOS")


def get_host_platform() -> Platform:
    """Find the architecture this script is running on."""
    s = platform.system()
    if s == "Linux":
        os_ = Os.LINUX
    elif s == "Darwin":
        os_ = Os.OSX
    elif s == "Windows":
        os_ = Os.WINDOWS
    else:
        raise ValueError("Don't know host OS {!r}".format(s))
    m = platform.machine()
    if m == "i386":
        cpu = Cpu.X86_32
    elif m == "x86_64":
        cpu = Cpu.X86_64
    else:
        raise ValueError("Don't know host CPU {!r}".format(m))
    return Platform(os_, cpu)


HOST_PLATFORM = get_host_platform()


# =============================================================================
# Config class, just to make sure we check the argument namespace properly
# =============================================================================
# https://stackoverflow.com/questions/42279063/python-typehints-for-argparse-namespace-objects  # noqa

class Config(object):
    # noinspection PyUnresolvedReferences
    def __init__(self, args: argparse.Namespace) -> None:
        # Architectures
        self.android_x86 = args.android_x86  # type: bool
        self.android_arm = args.android_arm  # type: bool
        self.linux_x86_64 = args.linux_x86_64  # type: bool
        self.osx_x86_64 = args.osx_x86_64  # type: bool
        self.windows_x86_64 = args.windows_x86_64  # type: bool
        self.ios = args.ios  # type: bool
        self.ios_simulator = args.ios_simulator  # type: bool
        self.ios_sdk = args.ios_sdk  # type: str

        # General
        self.show_config_only = args.show_config_only  # type: bool
        self.root_dir = args.root_dir  # type: str
        self.nparallel = args.nparallel  # type: int
        self.force = args.force  # type: bool
        self.verbose = args.verbose  # type: int
        self.src_rootdir = join(self.root_dir, "src")  # type: str

        # Qt
        # - git repository in src/qt5
        # - build to multiple directories off root
        # - each is (1) built into the "*_build" directory, then installed
        #   (via "make install") to the "*_install" directory.
        # - One points Qt Creator to "*_install/bin/qmake" to give it a Qt
        #   architecture "kit".
        self.qt_git_url = args.qt_git_url  # type: str
        self.qt_git_branch = args.qt_git_branch  # type: str
        self.qt_git_commit = args.qt_git_commit  # type: str
        self.qt_openssl_static = args.qt_openssl_static  # type: bool
        self.qt_src_gitdir = join(self.src_rootdir,
                                  args.qt_src_dirname)  # type: str  # noqa

        # Android SDK/NDK
        # - installed independently by user
        # - used for cross-compilation to Android targets
        self.android_api_number = args.android_api_number  # type: int
        self.android_sdk_root = args.android_sdk_root  # type: str
        self.android_ndk_root = args.android_ndk_root  # type: str
        self.android_ndk_host = args.android_ndk_host  # type: str
        self.android_toolchain_version = args.android_toolchain_version  # type: str  # noqa
        self.android_api = "android-{}".format(self.android_api_number)
        # ... see $ANDROID_SDK_ROOT/platforms/

        # OpenSSL
        # - download tar file to src/openssl
        # - built to multiple directories off root
        self.openssl_version = args.openssl_version  # type: str
        self.openssl_src_url = args.openssl_src_url  # type: str
        self.openssl_android_script_url = args.openssl_android_script_url  # type: str  # noqa
        # ... derived:
        self.openssl_src_dir = join(self.src_rootdir, "openssl")
        self.openssl_src_filename = "openssl-{}.tar.gz".format(
            self.openssl_version)
        self.openssl_src_fullpath = join(self.openssl_src_dir,
                                         self.openssl_src_filename)
        self.openssl_android_script_fullpath = join(
            self.openssl_src_dir, "Setenv-android.sh")

        # SQLCipher
        # - git repository in "src"
        # - single build in situ; we make the amalgamation file "sqlite3.c",
        #   and as a bonus the "sqlcipher" executable for the host machine, but
        #   the latter isn't part of CamCOPS's use of SQLCipher (CamCOPS just
        #   uses the amalgamation file, which is platform-independent).
        self.sqlcipher_git_url = args.sqlcipher_git_url  # type: str
        self.sqlcipher_git_commit = args.sqlcipher_git_commit  # type: str
        self.sqlcipher_src_gitdir = join(self.src_rootdir, "sqlcipher")  # type: str  # noqa

        if USE_BOOST:
            # Boost
            # - download tar file to src/boost
            # - unpack to boost/...
            self.boost_version = args.boost_version  # type: str
            self.boost_src_url = args.boost_src_url  # type: str
            # ... derived:
            boost_version_underscores = self.boost_version.replace(".", "_")
            self.boost_src_dir = join(self.src_rootdir, "boost")
            self.boost_src_filename = "boost_{}.tar.xz".format(
                boost_version_underscores)
            self.boost_src_fullpath = join(self.boost_src_dir,
                                           self.boost_src_filename)
            self.boost_dest_dir = join(self.root_dir, "boost")
            self.boost_root = join(self.boost_dest_dir,
                                   "boost_" + boost_version_underscores)
            self.boost_include_dir = self.boost_root
            self.boost_library_dir = join(self.boost_root, "libs")

        # Armadillo
        # - download tar file to src/armadillo
        # - unpack to armadillo/...
        # - build -- ABANDONED, lots of dependencies
        if USE_ARMADILLO:
            self.arma_version = args.arma_version  # type: str
            self.arma_src_url = args.arma_src_url  # type: str
            # ... derived:
            arma_w_version = "armadillo-{}".format(self.arma_version)
            self.arma_src_dir = join(self.src_rootdir, "armadillo")
            self.arma_src_filename = arma_w_version + ".tar.xz"
            self.arma_src_fullpath = join(self.arma_src_dir,
                                          self.arma_src_filename)
            self.arma_dest_dir = join(self.root_dir, "armadillo")
            self.arma_working_dir = join(self.arma_dest_dir, arma_w_version)
            self.arma_include_dir = join(self.arma_working_dir, "include")
            self.arma_lib = join(self.arma_working_dir, "libarmadillo.so")

        if USE_MLPACK:
            # MLPACK
            # - git repository in src/mlpack
            # - CMake to build BUT needs compilation (+ cross-compilation)
            self.mlpack_git_url = args.mlpack_git_url  # type: str
            self.mlpack_git_commit = args.mlpack_git_commit  # type: str
            self.mlpack_src_gitdir = join(self.src_rootdir, "mlpack")  # type: str  # noqa
            self.build_mlpack = args.build_mlpack  # type: bool

        if USE_EIGEN:
            self.eigen_version = args.eigen_version  # type: str
            self.eigen_src_url = (
                "http://bitbucket.org/eigen/eigen/get/{}.tar.gz".format(
                    self.eigen_version)
            )
            self.eigen_src_dir = join(self.src_rootdir, "eigen")
            self.eigen_src_fullpath = join(
                self.eigen_src_dir,
                "eigen-{}.tar.gz".format(self.eigen_version))
            self.eigen_unpacked_dir = join(self.root_dir, "eigen")

    def set_android_env(self,
                        env: Dict[str, str],
                        platform_: Platform) -> None:
        android_sysroot = self.android_sysroot(platform_)
        android_toolchain = self.android_toolchain(platform_)

        env["ANDROID_API"] = self.android_api
        env["ANDROID_API_VERSION"] = self.android_api
        env["ANDROID_ARCH"] = platform_.android_arch_full
        env["ANDROID_DEV"] = join(android_sysroot, "usr")
        env["ANDROID_EABI"] = self.android_eabi(platform_)
        env["ANDROID_NDK_ROOT"] = self.android_ndk_root
        env["ANDROID_SDK_ROOT"] = self.android_sdk_root
        env["ANDROID_SYSROOT"] = android_sysroot
        env["ANDROID_TOOLCHAIN"] = android_toolchain
        env["AR"] = self.android_ar(platform_)
        env["ARCH"] = platform_.android_arch_short
        env["CC"] = self.android_cc(platform_)
        env["PATH"] = "{}{}{}".format(android_toolchain, os.pathsep,
                                      env["PATH"])
        env["SYSROOT"] = android_sysroot
        env["NDK_SYSROOT"] = android_sysroot

    def set_ios_env(self, env: Dict[str, str], platform_: Platform) -> None:
        # https://gist.github.com/foozmeat/5154962
        encoding = sys.getdefaultencoding()
        developer = (
            subprocess.check_output([XCODE_SELECT, "-print-path"])
            .decode(encoding)
            .strip()
        )

        env["BUILD_TOOLS"] = developer
        env["CC"] = "{cc} -arch {arch}".format(
            cc=os.path.join(developer, 'usr', 'bin', 'gcc'),
            arch=platform_.ios_arch
        )
        env["CROSS_TOP"] = os.path.join(
            developer,
            "Platforms",
            "{}.platform".format(platform_.ios_platform_name),
            "Developer"
        )
        env["CROSS_SDK"] = "{plt}{sdkv}.sdk".format(
            plt=platform_.ios_platform_name,
            sdkv=self.ios_sdk,
            # ... can be blank; e.g. iPhoneOS9.3.sdk symlinks to iPhoneOS.sdk
        )
        env["PLATFORM"] = platform_.ios_platform_name

    def __repr__(self) -> str:
        elements = ["    {}={}".format(k, repr(v))
                    for k, v in self.__dict__.items()]
        elements.sort()
        return "{q}(\n{e}\n)".format(q=self.__class__.__qualname__,
                                     e=",\n".join(elements))

    def get_openssl_rootdir_workdir(self,
                                    platform_: Platform) -> Tuple[str, str]:
        """
        Calculates local OpenSSL directories.
        """
        rootdir = join(self.root_dir,
                       "openssl_{}_build".format(platform_.dirpart))
        workdir = join(rootdir, "openssl-{}".format(self.openssl_version))
        return rootdir, workdir

    def android_eabi(self, platform_: Platform) -> str:
        if platform_.cpu_x86_family:
            return "{}-{}".format(
                platform_.android_arch_short,
                self.android_toolchain_version)  # e.g. x86-4.9
            # For toolchain version: ls $ANDROID_NDK_ROOT/toolchains
            # ... "-android-arch" and "-android-toolchain-version" get
            # concatenated, I think; for example, this gives the toolchain
            # "x86_64-4.9"
        elif platform_.cpu_arm_family:
            # but ARM ones look like "arm-linux-androideabi-4.9"
            return "{}-linux-androideabi-{}".format(
                platform_.android_arch_short,
                self.android_toolchain_version)
        else:
            raise ValueError("Unknown CPU family")

    def android_sysroot(self, platform_: Platform) -> str:
        return join(self.android_ndk_root, "platforms",
                    self.android_api, platform_.android_arch_full)

    def android_toolchain(self, platform_: Platform) -> str:
        return join(self.android_ndk_root, "toolchains",
                    self.android_eabi(platform_),
                    "prebuilt", self.android_ndk_host, "bin")

    def android_ar(self, platform_: Platform) -> str:
        if platform_.cpu == Cpu.X86_32:
            return join(self.android_toolchain(platform_),
                        "i686-linux-android-gcc-ar")
        elif platform_.cpu == Cpu.ARM_V7:
            return join(self.android_toolchain(platform_),
                        "arm-linux-androideabi-gcc-ar")
        else:
            raise ValueError("Don't know how to build for Android on " +
                             platform_.cpu)

    def android_cc(self, platform_: Platform) -> str:
        if platform_.cpu == Cpu.X86_32:
            return join(self.android_toolchain(platform_),
                        "i686-linux-android-gcc-{}".format(
                            self.android_toolchain_version))
        elif platform_.cpu == Cpu.ARM_V7:
            return join(self.android_toolchain(platform_),
                        "arm-linux-androideabi-gcc-{}".format(
                            self.android_toolchain_version))
        else:
            raise ValueError("Don't know how to build for Android on " +
                             platform_.cpu)

    def convert_android_lib_a_to_so(self, lib_a_fullpath: str,
                                    platform_: Platform) -> str:
        # https://stackoverflow.com/questions/3919902/method-of-converting-a-static-library-into-a-dynamically-linked-library  # noqa
        libprefix = "lib"
        directory, filename = split(lib_a_fullpath)
        basename, ext = os.path.splitext(filename)
        if not basename.startswith(libprefix):
            raise ValueError("Don't know how to convert library " +
                             repr(lib_a_fullpath))
        libname = basename[len(libprefix):]
        newlibbasename = libprefix + libname + ".so"
        newlibfilename = join(directory, newlibbasename)
        compiler = self.android_cc(platform_)
        run([
            compiler,
            "-o", newlibfilename,
            "-shared",
            "-Wl,--whole-archive",
            "-Wl,-soname," + newlibbasename,
            lib_a_fullpath,
            "-Wl,--no-whole-archive",
            # "-L{}".format(directory),
            # "-l{}".format(libname),
            "--sysroot={}".format(self.android_sysroot(platform_)),
        ])
        platform_.verify_elf(newlibfilename)
        return newlibfilename

    def qt_build_dir(self, platform_: Platform) -> str:
        return join(self.root_dir, "qt_{}_build".format(platform_.dirpart))

    def qt_install_dir(self, platform_: Platform) -> str:
        return join(self.root_dir, "qt_{}_install".format(platform_.dirpart))


# =============================================================================
# Ancillary
# =============================================================================

@contextmanager
def pushd(directory: str) -> None:
    previous_dir = os.getcwd()
    chdir(directory)
    yield
    chdir(previous_dir)


def make_copy_paste_cmd(args: List[str]) -> str:
    return " ".join(shlex.quote(x) for x in args)


def make_copy_paste_env(env: Dict[str, str], windows: bool = False) -> str:
    cmd = "set" if windows else "export"
    return (
        "\n".join("{cmd} {k}={v}".format(
            cmd=cmd,
            k=shlex.quote(k),
            v=shlex.quote(v)
        ) for k, v in env.items()))


def run(args: List[str],
        env: Dict[str, str] = None,
        get_output: bool = False,
        encoding: str = sys.getdefaultencoding()) -> Tuple[str, str]:
    """
    Runs an external process.
    """
    log.info("From directory {}, running external command: {}".format(
        repr(os.getcwd()), args))
    copy_paste_cmd = make_copy_paste_cmd(args)
    csep = "=" * 79
    esep = "-" * 79
    if env is not None:
        log.info("Using environment: \n" + pformat(env))
        copy_paste_env = make_copy_paste_env(env)
        log.debug(
            "Copy/paste version of environment:\n{esep}\n{env}\n{esep}".format(
                env=copy_paste_env, esep=esep))
    log.debug("Copy/paste version of command:\n{csep}\n{cmd}\n{csep}".format(
        cmd=copy_paste_cmd, csep=csep))
    if get_output:
        p = subprocess.run(args, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=True)
        return p.stdout.decode(encoding), p.stderr.decode(encoding)
    else:
        subprocess.check_call(args, env=env)
        return "", ""


def replace(filename: str, text_from: str, text_to: str) -> None:
    """
    Replaces text in a file.
    """
    log.info("Amending {} from {} to {}".format(
        filename, repr(text_from), repr(text_to)))
    with open(filename) as infile:
        contents = infile.read()
    contents = contents.replace(text_from, text_to)
    with open(filename, 'w') as outfile:
        outfile.write(contents)


def require(command: str) -> None:
    """
    Checks that an external command is available, or raises an exception.
    """
    if not shutil.which(command):
        log.info("""
If core commands are missing:

OS/X
-------------------------------------------------------------------------------
cmake             brew update && brew install cmake
gobjdump          brew update && brew install binutils
        """)
        raise ValueError("Missing OS command: {}".format(command))


def replace_multiple(filename: str,
                     replacements: List[Tuple[str, str]]) -> None:
    """
    Replaces multiple from/to strings within a file.
    """
    with open(filename) as infile:
        contents = infile.read()
    for text_from, text_to in replacements:
        log.info("Amending {} from {} to {}".format(
            filename, repr(text_from), repr(text_to)))
        contents = contents.replace(text_from, text_to)
    with open(filename, 'w') as outfile:
        outfile.write(contents)


def mkdir_p(path: str) -> None:
    """
    Makes a directory, and any other necessary directories (mkdir -p).
    """
    log.info("mkdir -p {}".format(path))
    os.makedirs(path, exist_ok=True)


def download_if_not_exists(url: str, filename: str) -> None:
    """
    Downloads a URL to a file, unless the file already exists.
    """
    if isfile(filename):
        log.info("No need to download, already have: {}".format(filename))
        return
    directory, basename = split(abspath(filename))
    mkdir_p(directory)
    log.info("Downloading from {} to {}".format(url, filename))
    urllib.request.urlretrieve(url, filename)


def root_path() -> str:
    """
    Returns the system root directory.
    """
    # http://stackoverflow.com/questions/12041525
    return abspath(os.sep)


def git_clone(prettyname: str, url: str, directory: str,
              branch: str = None,
              commit: str = None) -> bool:
    """
    Fetches a Git repository, unless we have it already.
    Returns: did we need to do anything?
    """
    if isdir(directory):
        log.info("Not re-cloning {} Git repository: using existing source "
                 "in {}".format(prettyname, directory))
        return False
    log.info("Fetching {} source from {} into {}".format(
        prettyname, url, directory))
    gitargs = ["git", "clone"]
    if branch:
        gitargs += ["--branch", branch]
    gitargs += [url, directory]
    run(gitargs)
    if commit:
        log.info("Resetting {} local Git repository to commit {}".format(
            prettyname, commit))
        run(["git",
             "-C", directory,
             "reset", "--hard", commit])
        # Using a Git repository that's not in the working directory:
        # https://stackoverflow.com/questions/1386291/git-git-dir-not-working-as-expected  # noqa
    return True


def untar_to_directory(tarfile: str, directory: str,
                       verbose: bool = False,
                       gzipped: bool = False,
                       skip_if_dir_exists: bool = True) -> None:
    if skip_if_dir_exists and isdir(directory):
        log.info("Skipping extraction of {} as directory {} exists".format(
            repr(tarfile), repr(directory)))
        return
    log.info("Extracting {} to {}".format(repr(tarfile), repr(directory)))
    mkdir_p(directory)
    flags = "-x"  # extract
    if verbose:
        flags += "v"  # verbose
    if gzipped:
        flags += "z"  # decompress using gzip
    flags += "f"  # filename follows
    flags = "-xvf" if verbose else "-xf"
    run([TAR, flags, tarfile, "-C", directory])
    # C change to directory DIR


def delete_cmake_cache(directory: str) -> None:
    cmake_cache = join(directory, "CMakeCache.txt")
    if isfile(cmake_cache):
        log.info("Deleting CMake cache {}".format(repr(cmake_cache)))
        os.remove(cmake_cache)


def copytree(srcdir: str, destdir: str, destroy: bool = False) -> None:
    log.info("Copying directory {} -> {}".format(repr(srcdir), repr(destdir)))
    if os.path.exists(destdir):
        if not destroy:
            raise ValueError("Destination exists!")
        if not os.path.isdir(destdir):
            raise ValueError("Destination exists but isn't a directory!")
        log.info("... removing old contents")
        shutil.rmtree(destdir)
        log.info("... now copying")
    shutil.copytree(srcdir, destdir)


def chdir(directory: str) -> None:
    log.debug("Entering directory {}".format(repr(directory)))
    os.chdir(directory)


# =============================================================================
# Building OpenSSL
# =============================================================================

def fetch_openssl(cfg: Config) -> None:
    """
    Downloads OpenSSL source code.
    """
    download_if_not_exists(cfg.openssl_src_url, cfg.openssl_src_fullpath)
    download_if_not_exists(cfg.openssl_android_script_url,
                           cfg.openssl_android_script_fullpath)


def build_openssl(cfg: Config, platform_: Platform) -> None:
    """
    Builds OpenSSL.

    The target_os parameter is paseed to OpenSSL's Configure script.
    Use "./Configure LIST" for all possibilities.

        https://wiki.openssl.org/index.php/Compilation_and_Installation
    """
    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------
    rootdir, workdir = cfg.get_openssl_rootdir_workdir(platform_)
    shared_lib_suffix = platform_.shared_lib_suffix()
    targets = [join(workdir, "libssl{}".format(shared_lib_suffix)),
               join(workdir, "libcrypto{}".format(shared_lib_suffix))]
    if not cfg.force and all(isfile(x) for x in targets):
        log.info("OpenSSL: All targets exist already: {}".format(targets))
        return

    untar_to_directory(cfg.openssl_src_fullpath, rootdir)

    # -------------------------------------------------------------------------
    # Configure options
    # -------------------------------------------------------------------------
    # The OpenSSL "config" sh script guesses the OS, then passes details
    # to its "Configure" Perl script.
    # For Android, OpenSSL suggest using their Setenv-android.sh script, then
    # running "config".
    # However, it does seem to be screwing up. Let's try Configure instead.

    # http://doc.qt.io/qt-5/opensslsupport.html
    target_os = ""
    if platform_.os == Os.ANDROID:
        if platform_.cpu == Cpu.ARM_V5:
            target_os = "android"  # ... NB "android" means ARMv5
        elif platform_.cpu == Cpu.ARM_V7:
            target_os = "android-armv7"
        else:
            target_os = "android-{}".format(platform_.cpu)
    elif platform_.os == Os.LINUX and platform_.cpu == Cpu.X86_64:
        target_os = "linux-x86_64"
    elif platform_.os == Os.OSX and platform_.cpu == Cpu.X86_64:
        # https://gist.github.com/tmiz/1441111
        target_os = "darwin64-x86_64-cc"
    elif platform_.os == Os.IOS:

        # https://gist.github.com/foozmeat/5154962
        # https://gist.github.com/felix-schwarz/c61c0f7d9ab60f53ebb0
        # https://gist.github.com/armadsen/b30f352a8d6f6c87a146
        # If Bitcode is later required, see the other ones above and
        # https://stackoverflow.com/questions/30722606/what-does-enable-bitcode-do-in-xcode-7  # noqa

        if platform_.cpu == Cpu.ARM_V8_64:
            target_os = "iphoneos-cross"
        elif platform_.cpu == Cpu.X86_64:
            target_os = "darwin64-x86_64-cc"

        # iOS specials
        run([
            SED,
            "-ie",
            "s!static volatile sig_atomic_t intr_signal;!static volatile intr_signal;!",  # noqa
            join(workdir, "crypto", "ui", "ui_openssl.c")
        ])

        # At some point (transiently!) we also got something like:
        #    ar  r ../../libcrypto.a o_names.o obj_dat.o obj_lib.o 
        #        obj_err.o obj_xref.
        # failing with:
        #     /usr/bin/ranlib: archive member: libcrypto.a(....o) size too 
        #         large (archive member extends past the end of the file)
        #     ar: internal ranlib command failed
        # ... not sure why.

    if not target_os:
        raise ValueError("Don't know how to make OpenSSL for " +
                         platform_.description)

    configure_args = [target_os] + OPENSSL_COMMON_OPTIONS
    if platform_.mobile:
        configure_args += [
            "no-hw",  # disable hardware support ("useful on mobile devices")
            "no-engine",  # disable hardware support ("useful on mobile devices")  # noqa
        ]
    # OpenSSL's Configure script applies optimizations by default.

    # -------------------------------------------------------------------------
    # Environment
    # -------------------------------------------------------------------------
    env = {  # clean environment
        'PATH': os.environ['PATH'],
    }

    if platform_.android:
        # https://wiki.openssl.org/index.php/Android
        # We're not using the Setenv-android.sh script, but replicating its
        # functions.
        cfg.set_android_env(env, platform_)
        # env["CROSS_COMPILE"] = "i686-linux-android-"
        env["FIPS_SIG"] = ""  # OK to leave blank if not building FIPS
        env["HOSTCC"] = "gcc"
        env["MACHINE"] = "i686"
        env["RELEASE"] = "2.6.37"  # ??
        env["SYSTEM"] = target_os
    elif platform_.ios:
        cfg.set_ios_env(env, platform_)

    # -------------------------------------------------------------------------
    # Makefile
    # -------------------------------------------------------------------------
    # https://wiki.openssl.org/index.php/Android
    makefile_org = join(workdir, "Makefile.org")
    replace(makefile_org,
            "install: all install_docs install_sw",
            "install: install_docs install_sw")

    # -------------------------------------------------------------------------
    # Configure (or config)
    # -------------------------------------------------------------------------
    chdir(workdir)
    use_configure = True  # Better!
    if use_configure or not platform_.android:
        # http://doc.qt.io/qt-5/opensslsupport.html
        run(["perl", join(workdir, "Configure")] + configure_args, env)
    else:
        # The "config" script guesses the OS then runs "Configure".
        # https://wiki.openssl.org/index.php/Android
        # and "If in doubt, on Unix-ish systems use './config'."
        # https://wiki.openssl.org/index.php/Compilation_and_Installation
        run([join(workdir, "config")] + configure_args, env)

    # -------------------------------------------------------------------------
    # Make
    # -------------------------------------------------------------------------
    # Have to remove version numbers from final library filenames:
    # http://doc.qt.io/qt-5/opensslsupport.html
    makefile = join(workdir, "Makefile")
    replace_multiple(makefile, [
        ('LIBNAME=$$i LIBVERSION=$(SHLIB_MAJOR).$(SHLIB_MINOR)',
            'LIBNAME=$$i'),
        ('LIBCOMPATVERSIONS=";$(SHLIB_VERSION_HISTORY)"', ''),
    ])
    run([MAKE, "depend", "-j", str(cfg.nparallel)], env)
    run([MAKE, "build_libs", "-j", str(cfg.nparallel)], env)

    # Testing:
    # - "Have I built for the right architecture?"
    #   http://stackoverflow.com/questions/267941
    #   http://stackoverflow.com/questions/1085137
    #
    #   file libssl.so
    #   objdump -a libssl.so  # or -x, or...
    #   readelf -h libssl.so
    #
    # - Compare to files on the Android emulator:
    #
    #   adb pull /system/lib/libz.so  # system
    #   adb pull /data/data/org.camcops.camcops/lib/  # ours
    #
    # ... looks OK

    for t in targets:
        platform_.verify_elf(t)


# =============================================================================
# Building Qt
# =============================================================================

def fetch_qt(cfg: Config) -> None:
    """
    Downloads Qt source code.
    """
    if not git_clone(prettyname="Qt",
                     url=cfg.qt_git_url,
                     branch=cfg.qt_git_branch,
                     commit=cfg.qt_git_commit,
                     directory=cfg.qt_src_gitdir):
        return
    chdir(cfg.qt_src_gitdir)
    run(["perl", "init-repository"])


def build_qt(cfg: Config, platform_: Platform) -> str:
    """
    Builds Qt.
    Returns the name of the "install" directory, where the installe qmake is.
    """
    # Android example at http://wiki.qt.io/Qt5ForAndroidBuilding
    # http://doc.qt.io/qt-5/opensslsupport.html
    # Windows: ?also http://simpleit.us/2010/05/30/enabling-openssl-for-qt-c-on-windows/  # noqa

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    # Linkage method of Qt itself?
    qt_linkage_static = platform_.desktop
    # NOT Android; dynamic linkage then bundling into single-file APK.

    # Means by which Qt links to OpenSSL?
    qt_openssl_linkage_static = cfg.qt_openssl_static and qt_linkage_static
    # If Qt is linked dynamically, we do not let it link to OpenSSL
    # statically (it won't work).

    if platform_.android:
        require("javac")  # try: sudo apt install openjdk-8-jdk
        # ... will be called by the make process; better to know now, since the
        # relevant messages are easily lost in the torrent
        require("ant")  # will be needed later; try: sudo apt install ant

    opensslrootdir, opensslworkdir = cfg.get_openssl_rootdir_workdir(platform_)
    openssl_include_root = join(opensslworkdir, "include")
    openssl_lib_root = opensslworkdir

    builddir = cfg.qt_build_dir(platform_)
    installdir = cfg.qt_install_dir(platform_)

    targets = [join(installdir, "bin", "qmake")]
    if not cfg.force and all(isfile(x) for x in targets):
        log.info("Qt: All targets exist already: {}".format(targets))
        return installdir

    # -------------------------------------------------------------------------
    # Environment
    # -------------------------------------------------------------------------
    env = {  # clean environment
        'PATH': os.environ['PATH'],
        'OPENSSL_LIBS': "-L{} -lssl -lcrypto".format(openssl_lib_root),
        # ... unnecessary? But suggested by Qt.
        # ... http://doc.qt.io/qt-4.8/ssl.html
    }

    # -------------------------------------------------------------------------
    # Directories
    # -------------------------------------------------------------------------
    log.info("Configuring {} build in {}".format(platform_.description,
                                                 builddir))
    mkdir_p(builddir)
    mkdir_p(installdir)

    # -------------------------------------------------------------------------
    # configure
    # -------------------------------------------------------------------------
    qt_config_args = [
        join(cfg.qt_src_gitdir, "configure"),

        # General options:
        "-I", openssl_include_root,  # OpenSSL
        "-L", openssl_lib_root,  # OpenSSL
        "-prefix", installdir,
    ]
    if qt_linkage_static:
        qt_config_args.append("-static")
        # makes a static Qt library (cf. default of "-shared")
        # ... NB ALSO NEEDS "CONFIG += static" in the .pro file

    android_arch_short = "?"
    if platform_.android:
        # We use a dynamic build of Qt (bundled into the APK), not a static
        # version; see android_compilation.txt
        if platform_.cpu == Cpu.X86_32:
            android_arch_short = "x86"
        elif platform_.cpu == Cpu.ARM_V7:
            android_arch_short = "armeabi-v7a"
        else:
            raise ValueError("Unknown CPU: {}".format(platform_.cpu))
        qt_config_args += [
            "-android-sdk", cfg.android_sdk_root,
            "-android-ndk", cfg.android_ndk_root,
            "-android-ndk-host", cfg.android_ndk_host,
            "-android-arch", android_arch_short,
            "-android-toolchain-version", cfg.android_toolchain_version,
            "-xplatform", "android-g++",
        ]
    elif platform_.linux:
        qt_config_args += [
            "-qt-xcb",  # use XCB source bundled with Qt?
            "-gstreamer", "1.0",  # gstreamer version; see notes at top of file
        ]
    elif platform_.osx:
        pass
    elif platform_.ios:
        # http://doc.qt.io/qt-5/building-from-source-ios.html
        # "A default build builds both the simulator and device libraries."
        qt_config_args += [
            "-xplatform", "macx-ios-clang"
        ]

    qt_config_args.extend(QT_CONFIG_COMMON_ARGS)

    # For testing a new OpenSSL build, have cfg.qt_openssl_static=False, or you
    # have to rebuild Qt every time... extremely slow.
    if qt_openssl_linkage_static:
        qt_config_args.append("-openssl-linked")  # OpenSSL
        # http://doc.qt.io/qt-4.8/ssl.html
        # http://stackoverflow.com/questions/20843180
    else:
        qt_config_args.append("-openssl")  # OpenSSL

    if cfg.verbose >= 1:
        qt_config_args.append("-v")  # verbose
    if cfg.verbose >= 2:
        qt_config_args.append("-v")  # more verbose

    chdir(builddir)
    run(qt_config_args)  # The configure step takes a few seconds.

    # -------------------------------------------------------------------------
    # make (can take several hours)
    # -------------------------------------------------------------------------
    log.info("Making Qt {} build into {}".format(platform_.description,
                                                 installdir))
    chdir(builddir)
    if platform_.android:
        cfg.set_android_env(env, platform_)
        # ... only need ANDROID_API_VERSION, ANDROID_NDK_ROOT, ANDROID_SDK_ROOT

    run([MAKE, "-j", str(cfg.nparallel)], env)

    # -------------------------------------------------------------------------
    # make install
    # -------------------------------------------------------------------------
    if platform_.android and FIX_QT_5_7_0_ANDROID_MAKE_INSTALL_BUG:
        # PROBLEM WITH "make install":
        #       mkdir: cannot create directory ‘/libs’: Permission denied
        # ... while processing qttools/src/qtplugininfo/Makefile
        # https://bugreports.qt.io/browse/QTBUG-45095
        # 1. Attempt to fix as follows:
        makefile = join(builddir, "qttools", "src", "qtplugininfo", "Makefile")
        baddir = join("$(INSTALL_ROOT)", "libs", android_arch_short, "")
        gooddir = join(installdir, "libs", android_arch_short, "")
        replace(makefile, " " + baddir, " " + gooddir)

    # 2. Using INSTALL_ROOT: bases the root of a filesystem off installdir
    # env["INSTALL_ROOT"] = installdir
    # http://stackoverflow.com/questions/8360609

    run([MAKE, "install"], env)
    # ... installs to installdir because of -prefix earlier
    return installdir


def make_missing_libqtforandroid_so(cfg: Config, platform_: Platform) -> None:
    qt_install_dir = cfg.qt_install_dir(platform_)
    parent_dir = join(qt_install_dir, "plugins", "platforms")
    starting_lib_dir = join(parent_dir, "android")
    starting_a_lib = join(starting_lib_dir, "libqtforandroid.a")
    newlib_path = cfg.convert_android_lib_a_to_so(starting_a_lib, platform_)
    _, newlib_basename = split(newlib_path)
    extra_copy_newlib = join(parent_dir, newlib_basename)
    shutil.copyfile(newlib_path, extra_copy_newlib)


# =============================================================================
# SQLCipher
# =============================================================================

def fetch_sqlcipher(cfg: Config) -> None:
    """
    Downloads OpenSSL source code.
    """
    git_clone(prettyname="SQLCipher",
              url=cfg.sqlcipher_git_url,
              commit=cfg.sqlcipher_git_commit,
              directory=cfg.sqlcipher_src_gitdir)


def build_sqlcipher(cfg: Config, platform_: Platform) -> None:
    """
    Builds SQLCipher, an open-source encrypted version of SQLite.
    Our source is the public version; our destination is an "amalgamation"
    .h and .c file (equivalent to the amalgamation sqlite3.h and sqlite3.c
    of SQLite itself). Actually, they have the same names, too.
    
    CROSS-COMPILATION OF SQLITE/SQLCIPHER:
    [1] https://vicente-hernando.appspot.com/sqlite3-cross-compile-arm-howto
    [2] https://discuss.zetetic.net/t/cross-compile-sqlicipher-for-arm/2104
    [3] https://github.com/sqlcipher/sqlcipher/issues/176
    """

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------
    destdir = join(cfg.root_dir,
                   "sqlcipher_" + platform_.dirpart,
                   "sqlcipher")  # this allows #include <sqlcipher/sqlite3.h>

    target_h = join(destdir, "sqlite3.h")
    target_c = join(destdir, "sqlite3.c")
    target_o = join(destdir, "sqlite3.o")
    target_exe = join(destdir, "sqlcipher")

    want_exe = not platform_.mobile

    all_targets = [target_c, target_h, target_o]
    if want_exe:
        all_targets.append(target_exe)
    if all(isfile(x) for x in all_targets):
        log.info("SQLCipher: all targets present; skipping ({})".format(
            all_targets))
        return

    log.info("Building SQLCipher...")
    copytree(cfg.sqlcipher_src_gitdir, destdir, destroy=True)

    # -------------------------------------------------------------------------
    # configure
    # -------------------------------------------------------------------------
    _, openssl_workdir = cfg.get_openssl_rootdir_workdir(platform_)
    openssl_include_dir = join(openssl_workdir, "include")
    # Compiler:
    cflags = [
        "-DSQLITE_HAS_CODEC",
        "-I{}".format(openssl_include_dir),
        # ... sqlite.c does e.g. "#include <openssl/rand.h>"
    ]
    # Linker:
    ldflags = ["-L{}".format(openssl_workdir)]

    link_openssl_statically = platform_.desktop
    # ... try for dynamic linking on Android
    if link_openssl_statically:
        # Not working:
        # static_openssl_lib = join(openssl_workdir, "libcrypto.a")
        # ldflags.append("-static")
        # ldflags.append("-l:libcrypto.a")
        # ... Note the colon! Search for ":filename" in "man ld"
        ldflags.append('-lcrypto')
    else:
        # make the executable load OpenSSL dynamically
        ldflags.append('-lcrypto')
    # Note that "--with-crypto-lib" isn't helpful here:
    # https://www.zetetic.net/blog/2013/6/27/sqlcipher-220-release.html

    trace_include = False
    if trace_include:
        cflags.append("-H")
    if platform_.android:
        cflags.append("--sysroot={}".format(cfg.android_sysroot(platform_)))
        # ... or configure will call ld which will say:
        # ld: error: cannot open crtbegin_dynamic.o: No such file or directory

    config_args = [
        # no quotes (they're fine on the command line but not here)
        join(destdir, "configure"),
        "--enable-tempstore=yes",
        # ... see README.md; equivalent to SQLITE_TEMP_STORE=2
        'CFLAGS={}'.format(" ".join(cflags)),
        'LDFLAGS={}'.format(" ".join(ldflags)),
    ]
    # By default, SQLCipher compiles with "-O2" optimizations under gcc; see
    # its "configure" script.

    # Platform-specific tweaks; cross-compilation
    if platform_.cpu == Cpu.ARM_V7:
        # arm? [1]
        # arm-linux? [2]
        config_args.append("--build=x86_64-unknown-linux")
        config_args.append("--host=arm-linux")
        # config_args.append("--prefix={}".format(cfg.android_sysroot(platform)))
    if platform_.android:
        config_args.append("CC=" + cfg.android_cc(platform_))
        # ... or we won't be cross-compiling

    chdir(destdir)
    run(config_args)
    
    # -------------------------------------------------------------------------
    # make
    # -------------------------------------------------------------------------
    chdir(destdir)
    if not isfile(target_c) or not isfile(target_h):
        run([MAKE, "sqlite3.c"])  # the amalgamation target
    if not isfile(target_exe) or not isfile(target_o):
        run([MAKE, "sqlite3.o"])  # for static linking
    if want_exe and not isfile(target_exe):
        run([MAKE, "sqlcipher"])  # the command-line executable

    # -------------------------------------------------------------------------
    # Check and report
    # -------------------------------------------------------------------------
    platform_.verify_elf(target_o)

    log.info("If successful, you should have the amalgation files:\n"
             "- {}\n"
             "- {}\n"
             "and the library:\n"
             "- {}\n"
             "and, on non-mobile platforms, the executable:\n"
             "- {}".format(target_c, target_h, target_o, target_exe))


# =============================================================================
# Boost
# =============================================================================

def fetch_boost(cfg: Config) -> None:
    """
    Downloads Boost source code.
    """
    download_if_not_exists(cfg.boost_src_url, cfg.boost_src_fullpath)


def build_boost(cfg: Config) -> None:
    """
    Unpacks Boost from source.
    Try to avoid anything needing compilation; if we can keep this to
    "headers-only" Boost, it will be cross-platform without further effort.
    """
    untar_to_directory(cfg.boost_src_fullpath, cfg.boost_dest_dir)


# =============================================================================
# Armadillo
# =============================================================================

def fetch_armadillo(cfg: Config) -> None:
    """
    Downloads Armadillo source code.
    There's also a Git repository at
        https://github.com/conradsnicta/armadillo-code
    but the download is the verified static snapshot.
    """
    download_if_not_exists(cfg.arma_src_url, cfg.arma_src_fullpath)


def build_armadillo(cfg: Config) -> None:
    untar_to_directory(cfg.arma_src_fullpath, cfg.arma_dest_dir)
    # run([CMAKE,
    #      # "-D", "ARMADILLO_LIBRARY={}".format(cfg.arma_lib),
    #      "-D", "ARMADILLO_INCLUDE_DIR={}".format(cfg.arma_include_dir),
    #      cfg.arma_working_dir])
    # run([MAKE, "-C", cfg.arma_working_dir])


# =============================================================================
# MLPACK
# =============================================================================

def fetch_mlpack(cfg: Config) -> None:
    """
    Downloads MLPACK source code.
    """
    git_clone(prettyname="MLPACK",
              url=cfg.mlpack_git_url,
              commit=cfg.mlpack_git_commit,
              directory=cfg.mlpack_src_gitdir)


def build_mlpack(cfg: Config) -> None:
    """
    Without building, there is no <mlpack/mlpack_export.hpp>
    
    We run cmake for MLPACK, telling it where Armadillo lives.
    
    If you get this:
        CMake Error at CMake/NewCXX11.cmake:4 (target_compile_features):
        target_compile_features no known features for CXX compiler
        "GNU"
    ... update cmake from 3.5.1
        https://stackoverflow.com/questions/38027292/configure-a-qt5-5-7-application-for-android-with-cmake
        https://bugreports.qt.io/browse/QTBUG-54666
    ... note that CMake 3.7.0 is the first to support Android cross-
        compilation, too
    ... e.g. from https://launchpad.net/ubuntu/+source/cmake
        ... hard to install.
        ... first >=3.7.0 is Ubuntu zesty
        ... no backports to xenial
        ... "pinning"
        ... or just manually install .deb files:
        
        sudo dpkg --install \
            cmake_3.7.2-1_amd64.deb \
            cmake-data_3.7.2-1_all.deb \
            libjsoncpp1_1.7.4-3_amd64.deb

        from
            https://launchpad.net/ubuntu/+source/cmake
            https://packages.ubuntu.com/zesty/libjsoncpp1
            
    ... no, still get error; aha:
        https://github.com/mlpack/mlpack/issues/796
    ... see CMAKE_CXX_FLAGS below
        ... no, would need more hacking of the CMakeLists.txt
    ... aha! Define FORCE_CXX11=1

    """  # noqa
    delete_cmake_cache(cfg.mlpack_src_gitdir)
    cmakelists = join(cfg.mlpack_src_gitdir, "CMakeLists.txt")
    replacements = [
        # The supplied version hard-codes the Boost versions (as of 2017-06-06,
        # to versions 1.49.0 through 1.55.0), asking for 1.49.
        (
            '''set(Boost_ADDITIONAL_VERSIONS
  "1.49.0" "1.50.0" "1.51.0" "1.52.0" "1.53.0" "1.54.0" "1.55.0")''',
            'set(Boost_ADDITIONAL_VERSIONS "{}")'.format(cfg.boost_version)
        ),
        # Note that FindBoost.cmake looks for
        #       boost_program_options
        #       boost_unit_test_framework
        #       boost_serialization
        # as libraries (and they require Boost compilation)...
        # ... BECAUSE they are marked as REQUIRED by MLPACK's CMakeLists.txt
        # We shouldn't need them, so as well as changing the Boost version,
        # we can remove the requirement:
        (
            """find_package(Boost 1.49
    COMPONENTS
      program_options
      unit_test_framework
      serialization
    REQUIRED
)""",
            "find_package(Boost {})".format(cfg.boost_version)
        ),
    ]
    replace_multiple(cmakelists, replacements)
    log.info("CMake version:")
    with pushd(cfg.mlpack_src_gitdir):
        run([CMAKE, "--version"])
        run([
            CMAKE,
            #  "-D", "ARMADILLO_LIBRARY={}".format(cfg.arma_lib),
            "-D", "ARMADILLO_INCLUDE_DIR={}".format(cfg.arma_include_dir),
            "-D", "BOOST_ROOT={}".format(cfg.boost_root),
            "-D", "BOOST_INCLUDEDIR={}".format(cfg.boost_include_dir),
            "-D", "BOOST_LIBRARYDIR={}".format(cfg.boost_library_dir),
            # "-D", "CMAKE_CXX_FLAGS=-I/usr/local/opt/llvm/include -std=c++11",
            "-D", "FORCE_CXX11=1"
            # "-D", "Boost_DEBUG=ON",  # tell FindBoost.cmake to be verbose
            # "-L",  # list variables
            # "--debug-output",
            # "--trace-expand",  # very verbose
            "-Wno-dev",  # turn off some warnings
            cfg.mlpack_src_gitdir
        ])


# =============================================================================
# Eigen
# =============================================================================

def fetch_eigen(cfg: Config) -> None:
    """
    Downloads Eigen.
    http://eigen.tuxfamily.org
    """
    download_if_not_exists(cfg.eigen_src_url, cfg.eigen_src_fullpath)


def build_eigen(cfg: Config) -> None:
    """
    'Build' simply means 'unpack' -- header-only template library.
    """
    untar_to_directory(tarfile=cfg.eigen_src_fullpath,
                       directory=cfg.eigen_unpacked_dir,
                       gzipped=True)


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """
    Main entry point.
    """
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT,
                        datefmt=LOG_DATEFMT)
    log.info("Running on {}".format(HOST_PLATFORM))
    HOST_PLATFORM.ensure_elf_reader()

    # -------------------------------------------------------------------------
    # Command-line arguments
    # -------------------------------------------------------------------------

    parser = argparse.ArgumentParser(
        description="Build Qt and other libraries for CamCOPS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # General
    general = parser.add_argument_group("General", "General options")
    default_root_dir = os.environ.get(ENVVAR_QT_BASE) or DEFAULT_ROOT_DIR
    general.add_argument(
        "--show_config_only", action="store_true",
        help="Show config, then quit")
    general.add_argument(
        "--root_dir", default=default_root_dir,
        help=(
            "Root directory for source and builds (default taken from "
            "environment variable {} if present)".format(ENVVAR_QT_BASE)
        )
    )
    general.add_argument(
        "--nparallel", type=int, default=multiprocessing.cpu_count(),
        help="Number of parallel processes to run")
    general.add_argument("--force", action="store_true", help="Force build")
    general.add_argument(
        "--verbose", "-v", type=int, default=1,
        help="Verbosity level")

    # Architectures
    archgroup = parser.add_argument_group(
        "Architecture",
        "Choose architecture for which to build")
    archgroup.add_argument(
        "--android_x86", action="store_true",
        help="An architecture target (Android under an Intel x86 emulator)")
    archgroup.add_argument(
        "--android_arm", action="store_true",
        help="An architecture target (Android under a ARM processor tablet)")
    archgroup.add_argument(
        "--linux_x86_64", action="store_true",
        help="An architecture target (native Linux with a 64-bit Intel CPU; "
             "check with 'lscpu' and 'uname -a'")
    archgroup.add_argument(
        "--osx_x86_64", action="store_true",
        help="An architecture target (Mac OS/X under an Intel 64-bit CPU; "
             "check with 'sysctl -a|grep cpu', and see "
             "https://support.apple.com/en-gb/HT201948 )")
    archgroup.add_argument(
        "--windows_x86_64", action="store_true",
        help="An architecture target (Windows with an Intel 64-bit CPU)"
    )
    archgroup.add_argument(
        "--ios", action="store_true",
        help="An architecture target (iOS with a 64-bit ARM processor)"
    )
    archgroup.add_argument(
        "--ios_simulator", action="store_true",
        help="An architecture target (iOS with an Intel 64-bit CPU, for the "
             "iOS simulator)"
    )
    archgroup.add_argument(
        "--ios_sdk", default="",
        help="iOS SDK to use (leave blank for system default)"
    )

    # Qt
    qt = parser.add_argument_group(
        "Qt",
        "Qt options [Qt must be built from source for SQLite support, and "
        "also if static OpenSSL linkage is desired; note that static OpenSSL "
        "linkage requires a Qt rebuild (slow!) if you rebuild OpenSSL]")
    qt.add_argument(
        "--qt_src_dirname", default=DEFAULT_QT_SRC_DIRNAME,
        help="Qt source directory")
    qt.add_argument(
        "--qt_git_url", default=DEFAULT_QT_GIT_URL,
        help="Qt Git URL")
    qt.add_argument(
        "--qt_git_branch", default=DEFAULT_QT_GIT_BRANCH,
        help="Qt Git branch")
    qt.add_argument(
        "--qt_git_commit", default=DEFAULT_QT_GIT_COMMIT,
        help="Qt Git commit")
    qt.add_argument(
        "--qt_openssl_static", dest="qt_openssl_static", action="store_true",
        help="Link OpenSSL statically (ONLY if Qt is statically linked) "
             "[True=static, False=dynamic]")
    qt.add_argument(
        "--qt_openssl_linked", dest="qt_openssl_static", action="store_false",
        help="Link OpenSSL dynamically [True=static, False=dynamic]")
    parser.set_defaults(qt_openssl_static=DEFAULT_QT_USE_OPENSSL_STATICALLY)

    # Android
    android = parser.add_argument_group(
        "Android",
        "Android options (NB you must install the Android SDK and NDK "
        "separately, BEFOREHAND)")
    android.add_argument(
        "--android_api_number", type=int, default=DEFAULT_ANDROID_API_NUM,
        help="Android API number")
    android.add_argument(
        "--android_sdk_root", default=DEFAULT_ANDROID_SDK,
        help="Android SDK root directory")
    android.add_argument(
        "--android_ndk_root", default=DEFAULT_ANDROID_NDK,
        help="Android NDK root directory")
    android.add_argument(
        "--android_ndk_host", default=DEFAULT_NDK_HOST,
        help="Android NDK host architecture")
    android.add_argument(
        "--android_toolchain_version", default=DEFAULT_TOOLCHAIN_VERSION,
        help="Android toolchain version")

    # OpenSSL
    openssl = parser.add_argument_group(
        "OpenSSL",
        "OpenSSL options [OpenSSL must be built from source to use it on "
        "Android; Qt needs OpenSSL somehow; CamCOPS uses OpenSSL]")
    openssl.add_argument(
        "--openssl_version", default=DEFAULT_OPENSSL_VERSION,
        help="OpenSSL version")
    openssl.add_argument(
        "--openssl_src_url", default=DEFAULT_OPENSSL_SRC_URL,
        help="OpenSSL source URL")
    openssl.add_argument(
        "--openssl_android_script_url",
        default=DEFAULT_OPENSSL_ANDROID_SCRIPT_URL,
        help="OpenSSL Android script source (URL) (not really unused)"
    )
    
    # SQLCipher
    sqlcipher = parser.add_argument_group(
        "SQLCipher",
        "SQLCipher options [CamCOPS uses SQLCipher]")
    sqlcipher.add_argument(
        "--sqlcipher_git_url", default=DEFAULT_SQLCIPHER_GIT_URL,
        help="SQLCipher Git URL")
    sqlcipher.add_argument(
        "--sqlcipher_git_commit", default=DEFAULT_SQLCIPHER_GIT_COMMIT,
        help="SQLCipher Git commit")

    # Boost (used by MLPACK)
    if USE_BOOST:
        boost = parser.add_argument_group(
            "Boost",
            "Boost C++ library options [MLPACK uses Boost]")
        boost.add_argument(
            "--boost_version", default=DEFAULT_BOOST_VERSION,
            help="Armadillo version")
        boost.add_argument(
            "--boost_src_url", default=DEFAULT_BOOST_SRC_URL,
            help="Armadillo source URL")

    # Armadillo (used by MLPACK)
    if USE_ARMADILLO:
        armadillo = parser.add_argument_group(
            "Armadillo",
            "Armadillo C++ library options [MLPACK uses Armadillo]")
        armadillo.add_argument(
            "--arma_version", default=DEFAULT_ARMA_VERSION,
            help="Armadillo version")
        armadillo.add_argument(
            "--arma_src_url", default=DEFAULT_ARMA_SRC_URL,
            help="Armadillo source URL")

    # MLPACK
    if USE_MLPACK:
        mlpack = parser.add_argument_group(
            "MLPACK",
            "MLPACK C++ library options [CamCOPS uses MLPACK]")
        mlpack.add_argument(
            "--mlpack_git_url", default=DEFAULT_MLPACK_GIT_URL,
            help="MLPACK Git URL")
        mlpack.add_argument(
            "--mlpack_git_commit", default=DEFAULT_MLPACK_GIT_COMMIT,
            help="MLPACK Git commit")
        mlpack.add_argument(
            "--build_mlpack", action="store_true",
            help="MLPACK: build (in isolation)")

    # Eigen
    if USE_EIGEN:
        eigen = parser.add_argument_group(
            "Eigen",
            "Eigen C++ template library [CamCOPS uses Eigen]")
        eigen.add_argument(
            "--eigen_version", default=DEFAULT_EIGEN_VERSION,
            help="Eigen version")

    args = parser.parse_args()  # type: argparse.Namespace

    # Calculated args

    cfg = Config(args)
    log.info("Args: {}".format(args))
    log.info("Config: {}".format(cfg))

    if cfg.show_config_only:
        sys.exit(0)

    # =========================================================================
    # Common requirements
    # =========================================================================
    require(CMAKE)
    require(MAKE)
    require(TAR)

    # =========================================================================
    # Fetch
    # =========================================================================
    fetch_qt(cfg)
    fetch_openssl(cfg)
    fetch_sqlcipher(cfg)
    if USE_BOOST:
        fetch_boost(cfg)
    if USE_ARMADILLO:
        fetch_armadillo(cfg)
    if USE_MLPACK:
        fetch_mlpack(cfg)
    if USE_EIGEN:
        fetch_eigen(cfg)

    # =========================================================================
    # Build
    # =========================================================================

    if USE_BOOST:
        build_boost(cfg)
    if USE_ARMADILLO:
        build_armadillo(cfg)
    if USE_MLPACK:
        build_mlpack(cfg)
    if USE_EIGEN:
        build_eigen(cfg)

    installdirs = []
    done_extra = False

    # noinspection PyShadowingNames
    def build_for(os: str, cpu: str) -> None:
        platform = Platform(os, cpu)
        build_openssl(cfg, platform)
        installdirs.append(build_qt(cfg, platform))
        if platform.android and ADD_SO_VERSION_OF_LIBQTFORANDROID:
            make_missing_libqtforandroid_so(cfg, platform)
        build_sqlcipher(cfg, platform)
        
    extras = " +SQLite/SQLCipher +OpenSSL"

    if cfg.android_x86:  # for x86 Android emulator
        log.info("Qt build: Android x86" + extras)
        build_for(Os.ANDROID, Cpu.X86_32)

    if cfg.android_arm:  # for native Android
        log.info("Qt build: Android ARM" + extras)
        build_for(Os.ANDROID, Cpu.ARM_V7)

    if cfg.linux_x86_64:  # for 64-bit Linux
        log.info("Qt build: Linux x86 64-bit" + extras)
        build_for(Os.LINUX, Cpu.X86_64)

    if cfg.osx_x86_64:  # for 64-bit Intel Mac OS/X
        # http://doc.qt.io/qt-5/osx.html
        log.info("Qt build: Mac OS/X x86 64-bit" + extras)
        build_for(Os.OSX, Cpu.X86_64)
        
    if cfg.windows_x86_64:
        # *** NOT IMPLEMENTED PROPERLY YET
        log.info("Qt build: Windows, Intel 64-bit" + extras)
        build_for(Os.WINDOWS, Cpu.X86_64)
        # *** cfg.windows*  # build_qt for Windows
        #   http://doc.qt.io/qt-5/windows-building.html
        #     http://www.holoborodko.com/pavel/2011/02/01/how-to-compile-qt-4-7-with-visual-studio-2010/

    if cfg.ios:
        # *** NOT IMPLEMENTED PROPERLY YET
        log.info("Qt build: iOS, 64-bit ARM" + extras)
        build_for(Os.IOS, Cpu.ARM_V8_64)

    if cfg.ios_simulator:
        # *** NOT IMPLEMENTED PROPERLY YET
        log.info("Qt build: iOS simulator, x64 64-bit" + extras)
        build_for(Os.IOS, Cpu.X86_64)
        # *** cfg.ios*  # build_qt for iOS (iPad, etc.)
        #     http://doc.qt.io/qt-5/building-from-source-ios.html
        #     http://doc.qt.io/qt-5/ios-support.html

    if not installdirs and not done_extra:
        log.warning("Nothing more to do. Run with --help argument for help.")
        sys.exit(1)

    log.info("""
===============================================================================
Now, in Qt Creator:
===============================================================================
1. Add Qt build
      Tools > Options > Build & Run > Qt Versions > Add
      ... browse to one of: {bindirs}
      ... and select "qmake".
2. Create kit
      Tools > Options > Build & Run > Kits > Add (manual)
      ... Qt version = the one you added in the preceding step
      ... compiler =
            for Android: Android GCC (i686-4.9)
      ... debugger =
            for Android: Android Debugger for GCC (i686-4.9)
Then for your project,
      - click on the "Projects" tab
      - Add Kit > choose the kit you created.
      - For Android:
        - Build Settings > Android APK > Details > Additional Libraries > Add

BUILD / RUNTIME REQUIREMENTS

- For Ubuntu, see compilation_linux.txt

- To build Android programs under Linux, also need:

    sudo apt install openjdk-8-jdk

- For debugging, consider:

    sudo apt install valgrind

    """.format(  # noqa
        bindirs=", ".join(join(x, "bin") for x in installdirs)
    ))
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        log.critical("External process failed:")
        traceback.print_exc()
        log.critical("If this is the first time you've had this error RE-RUN "
                     "THE SCRIPT; sometimes Qt builds fail then pick "
                     "themselves up the next time.")
        sys.exit(1)
