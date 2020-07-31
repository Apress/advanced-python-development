# Functions from Pip https://github.com/pypa/pip/blob/800f866600968997dd6d9e49076b401784195123/src/pip/_internal/utils/appdirs.py  # noqa: E501


# Copyright (c) 2008-2019 The pip developers (see AUTHORS.txt file)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# Authors of the relevant code appear to be
#   Chris Jerdonek <chris.jerdonek@gmail.com>
#   cytolentino <ctolentino8@bloomberg.net>
#   Donald Stufft <donald@stufft.io>
#   Maxim Kurnikov <maxim.kurnikov@gmail.com>
#   Mickaël Schoentgen <mschoentgen@nuxeo.com>
#   Monica Baluna <mbaluna@bloomberg.net>
#   Pradyun Gedam <pradyunsg@gmail.com>
# but thanks go to all contributors to pip


# This contains modifications to simplify dependencies, please do not
# report any bugs against the official version that only affect
# this implementation

from __future__ import absolute_import

import ctypes
import os
import sys

from typing import List


WINDOWS = sys.platform.startswith("win") or (sys.platform == "cli" and os.name == "nt")


def expanduser(path):
    # type: (str) -> str
    """
    Expand ~ and ~user constructions.
    Includes a workaround for https://bugs.python.org/issue14768
    """
    expanded = os.path.expanduser(path)
    if path.startswith("~/") and expanded.startswith("//"):
        expanded = expanded[1:]
    return expanded


def user_data_dir(appname, roaming=False):
    # type: (str, bool) -> str
    r"""
    Return full path to the user-specific data dir for this application.
        "appname" is the name of application.
            If None, just the system directory is returned.
        "roaming" (boolean, default False) can be set True to use the Windows
            roaming appdata directory. That means that for users on a Windows
            network setup for roaming profiles, this user data will be
            sync'd on login. See
            <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx>
            for a discussion of issues.
    Typical user data directories are:
        macOS:                  ~/Library/Application Support/<AppName>
                                if it exists, else ~/.config/<AppName>
        Unix:                   ~/.local/share/<AppName>    # or in
                                $XDG_DATA_HOME, if defined
        Win XP (not roaming):   C:\Documents and Settings\<username>\ ...
                                ...Application Data\<AppName>
        Win XP (roaming):       C:\Documents and Settings\<username>\Local ...
                                ...Settings\Application Data\<AppName>
        Win 7  (not roaming):   C:\\Users\<username>\AppData\Local\<AppName>
        Win 7  (roaming):       C:\\Users\<username>\AppData\Roaming\<AppName>
    For Unix, we follow the XDG spec and support $XDG_DATA_HOME.
    That means, by default "~/.local/share/<AppName>".
    """
    if WINDOWS:
        const = roaming and "CSIDL_APPDATA" or "CSIDL_LOCAL_APPDATA"
        path = os.path.join(os.path.normpath(_get_win_folder(const)), appname)
    elif sys.platform == "darwin":
        path = (
            os.path.join(expanduser("~/Library/Application Support/"), appname)
            if os.path.isdir(
                os.path.join(expanduser("~/Library/Application Support/"), appname)
            )
            else os.path.join(expanduser("~/.config/"), appname)
        )
    else:
        path = os.path.join(
            os.getenv("XDG_DATA_HOME", expanduser("~/.local/share")), appname
        )

    return path


def user_config_dir(appname, roaming=True):
    # type: (str, bool) -> str
    """Return full path to the user-specific config dir for this application.
        "appname" is the name of application.
            If None, just the system directory is returned.
        "roaming" (boolean, default True) can be set False to not use the
            Windows roaming appdata directory. That means that for users on a
            Windows network setup for roaming profiles, this user data will be
            sync'd on login. See
            <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx>
            for a discussion of issues.
    Typical user data directories are:
        macOS:                  same as user_data_dir
        Unix:                   ~/.config/<AppName>
        Win *:                  same as user_data_dir
    For Unix, we follow the XDG spec and support $XDG_CONFIG_HOME.
    That means, by default "~/.config/<AppName>".
    """
    if WINDOWS:
        path = user_data_dir(appname, roaming=roaming)
    elif sys.platform == "darwin":
        path = user_data_dir(appname)
    else:
        path = os.getenv("XDG_CONFIG_HOME", expanduser("~/.config"))
        path = os.path.join(path, appname)

    return path


# for the discussion regarding site_config_dirs locations
# see <https://github.com/pypa/pip/issues/1733>
def site_config_dirs(appname):
    # type: (str) -> List[str]
    r"""Return a list of potential user-shared config dirs for this application.
        "appname" is the name of application.
    Typical user config directories are:
        macOS:      /Library/Application Support/<AppName>/
        Unix:       /etc or $XDG_CONFIG_DIRS[i]/<AppName>/ for each value in
                    $XDG_CONFIG_DIRS
        Win XP:     C:\Documents and Settings\All Users\Application ...
                    ...Data\<AppName>\
        Vista:      (Fail! "C:\ProgramData" is a hidden *system* directory
                    on Vista.)
        Win 7:      Hidden, but writeable on Win 7:
                    C:\ProgramData\<AppName>\
    """
    if WINDOWS:
        path = os.path.normpath(_get_win_folder("CSIDL_COMMON_APPDATA"))
        pathlist = [os.path.join(path, appname)]
    elif sys.platform == "darwin":
        pathlist = [os.path.join("/Library/Application Support", appname)]
    else:
        # try looking in $XDG_CONFIG_DIRS
        xdg_config_dirs = os.getenv("XDG_CONFIG_DIRS", "/etc/xdg")
        if xdg_config_dirs:
            pathlist = [
                os.path.join(expanduser(x), appname)
                for x in xdg_config_dirs.split(os.pathsep)
            ]
        else:
            pathlist = []

        # always look in /etc directly as well
        pathlist.append("/etc")

    return pathlist


# -- Windows support functions --


def _get_win_folder(csidl_name):
    # type: (str) -> str
    # On Python 2, ctypes.create_unicode_buffer().value returns "unicode",
    # which isn't the same as str in the annotation above.
    csidl_const = {
        "CSIDL_APPDATA": 26,
        "CSIDL_COMMON_APPDATA": 35,
        "CSIDL_LOCAL_APPDATA": 28,
    }[csidl_name]

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

    # Downgrade to short path name if have highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = False
    for c in buf:
        if ord(c) > 255:
            has_high_char = True
            break
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    # The type: ignore is explained under the type annotation for this function
    return buf.value  # type: ignore
