#!/bin/env python
# -*- encoding: utf-8 -*-
"""
vim-dot-files deployment script.

Author:     Kay Zheng <l04m33@gmail.com>
License:    MIT (http://l04m33.mit-license.org)

"""

from __future__ import print_function

import os
import sys


VIMRC_NAME = '.vimrc'
VIM_DIR_NAME = '.vim'
VIM_TMP_DIR_NAME = '.vim_tmp'


def _get_dot_files_path():
    script_name = sys.argv[0]
    script_path = os.path.abspath(script_name)
    return os.path.dirname(script_path)


def _get_home():
    home = os.environ.get('HOME', None)
    if home is None:
        raise RuntimeError('Cannot determine $HOME')
    return os.path.realpath(home)


def _check_dot_files_path(home, dot_files_path):
    if os.path.join(home, VIM_DIR_NAME) != dot_files_path:
        raise RuntimeError('Invalid dot files location: {}'
                           .format(dot_files_path))


if __name__ == '__main__':
    deployed_path = _get_dot_files_path()
    print('Deployed path: {}'.format(deployed_path))

    user_home = _get_home()
    _check_dot_files_path(user_home, deployed_path)

    deploy_commands = [
        "ln -s '{}' '{}'"
        .format(os.path.join(deployed_path, VIMRC_NAME),
                os.path.join(user_home, VIMRC_NAME)),

        "mkdir '{}'"
        .format(os.path.join(deployed_path, VIM_TMP_DIR_NAME)),

        "cd '{}'; git submodule update --init"
        .format(deployed_path),

        "vim +PluginInstall +qall",
    ]

    for cmd in deploy_commands:
        if os.system(cmd) != 0:
            raise RuntimeError('Failed to execute deploy command: {}'
                               .format(cmd))

    print('All done.')
