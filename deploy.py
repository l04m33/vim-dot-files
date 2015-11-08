#!/bin/env python3
# -*- encoding: utf-8 -*-
"""
vim-dot-files deployment script.

Author:     Kay Zheng <l04m33@gmail.com>
License:    MIT (http://l04m33.mit-license.org)

"""

import os
import sys
import itertools


VIM_DIR_NAME = '.vim'
VIM_TMP_DIR_NAME = '.vim_tmp'
BUNDLE_DIR_NAME = 'bundle'
VUNDLE_DIR_NAME = 'Vundle.vim'
VUNDLE_GIT_URL = 'https://github.com/VundleVim/Vundle.vim.git'


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


def _mkdir(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def _git_clone(url, path):
    if os.path.isdir(path) and os.path.isdir(os.path.join(path, '.git')):
        return
    cmd = "git clone '{}' '{}'".format(url, path)
    if os.system(cmd) != 0:
        raise RuntimeError(
            "Failed to clone '{}' into '{}'".format(url, path))


if __name__ == '__main__':
    deployed_path = _get_dot_files_path()
    print('Deployed path: {}'.format(deployed_path))

    user_home = _get_home()
    _check_dot_files_path(user_home, deployed_path)

    _mkdir(os.path.join(user_home, VIM_TMP_DIR_NAME))
    _mkdir(os.path.join(deployed_path, BUNDLE_DIR_NAME))

    clone_into = itertools.accumulate(
        [deployed_path, BUNDLE_DIR_NAME, VUNDLE_DIR_NAME],
        os.path.join)
    clone_into = list(clone_into)[-1]
    _git_clone(VUNDLE_GIT_URL, clone_into)

    extra_deploy_commands = [
        "vim +PluginInstall +qall",
    ]

    for cmd in extra_deploy_commands:
        if os.system(cmd) != 0:
            raise RuntimeError('Failed to execute deploy command: {}'
                               .format(cmd))

    print('All done.')
