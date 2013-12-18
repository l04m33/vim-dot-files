#!/bin/env python
# -*- encoding: utf-8 -*-
"""
vim-dot-files deploment script.

Author:     Kay Zheng <l04m33@gmail.com>
License:    MIT (http://l04m33.mit-license.org)

"""

from __future__ import print_function

import os
import sys


def _get_dot_files_path():
    script_name = sys.argv[0]
    script_path = os.path.abspath(script_name)
    return os.path.dirname(script_path)


def _get_home():
    home = os.environ.get('HOME', None)
    if home is None:
        raise RuntimeError('Cannot determine $HOME')
    if home.endswith(os.path.sep):
        home = home[0:-1]
    return home


def _check_dot_files_path(home, dot_files_path):
    if home + os.path.sep + '.vim' != dot_files_path:
        raise RuntimeError('Invalid dot files location: {}'
                           .format(dot_files_path))


VIMRC_NAME = '.vimrc'


if __name__ == '__main__':
    deployed_path = _get_dot_files_path()
    print('Deployed path: {}'.format(deployed_path))

    user_home = _get_home()
    _check_dot_files_path(user_home, deployed_path)

    deploy_commands = [
        "ln -s '{}' '{}'"
        .format(deployed_path + os.path.sep + VIMRC_NAME,
            user_home + os.path.sep + VIMRC_NAME),
        "cd '{}'; git submodule update --init"
        .format(deployed_path),
        'vim +BundleInstall +qall',
    ]

    for cmd in deploy_commands:
        if os.system(cmd) != 0:
            raise RuntimeError('Failed to execute deploy command: {}'
                               .format(cmd))

    print('All done.')
