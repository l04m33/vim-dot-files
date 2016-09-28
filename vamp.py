#!/bin/env python3
# -*- encoding: utf-8 -*-

import os
import sys
import json
import subprocess
import logging
from collections import namedtuple


SCRIPT_NAME = os.path.splitext(os.path.basename(sys.argv[0]))[0]
WORKING_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
PACK_DIR_NAME = 'pack'
REPO_DIR_NAME = 'repo'
CONFIG_FILE_NAME = 'vamp.json'


def logger(name=''):
    if name == '':
        name = SCRIPT_NAME
    else:
        name = '.'.join([SCRIPT_NAME, name])

    return logging.getLogger(name)


def ensure_dir_exists(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass


def get_repo_dir(repo_name):
    return os.path.join(WORKING_DIR, REPO_DIR_NAME, repo_name)


def get_package_dir(package_name):
    return os.path.join(WORKING_DIR, PACK_DIR_NAME, package_name)


def get_load_type_dir(package_name, load_type):
    return os.path.join(get_package_dir(package_name), load_type)


def get_plugin_dir(package_name, load_type, plugin_name):
    return os.path.join(
            get_load_type_dir(package_name, load_type),
            plugin_name)


def get_config_file():
    return os.path.join(WORKING_DIR, CONFIG_FILE_NAME)


def read_config(conf_file):
    logger().debug('Reading config file \'{}\''.format(conf_file))
    with open(conf_file, mode='r') as cf:
        return json.load(cf)


def indent_lines(text, n):
    return os.linesep.join([(' ' * n) + line for line in text.split('\n')])


def get_github_repo_name(plugin):
    return plugin['source'].split('/')[1]


def install_plugin_from_github(package_name, load_type, plugin):
    repo_name = get_github_repo_name(plugin)
    repo_dir = get_repo_dir(repo_name)
    if os.path.isdir(repo_dir) and os.path.isdir(os.path.join(repo_dir, '.git')):
        logger().warning(indent_lines('Plugin repo \'{}\' exists.', 6).format(repo_name))
    else:
        repo_url = '/'.join(['https://github.com', plugin['source']]) + '.git'
        r = subprocess.run(['git', 'clone', repo_url, repo_dir],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True)
        if r.returncode != 0:
            logger('git').error(indent_lines(r.stderr, 6))
            clean_up_plugin(package_name, load_type, plugin)
            return

    if 'subpath' in plugin:
        ln_target = os.path.join(repo_dir, plugin['subpath'])
    else:
        ln_target = repo_dir

    try:
        os.symlink(
                ln_target,
                get_plugin_dir(package_name, load_type, repo_name),
                target_is_directory=True)
    except Exception as e:
        logger('symlink').error(indent_lines(repr(e), 6))


def update_plugin_from_github(package_name, load_type, plugin):
    repo_name = get_github_repo_name(plugin)
    repo_dir = get_repo_dir(repo_name)
    r = subprocess.run('cd \'{}\'; git pull'.format(repo_dir),
            shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
    if r.returncode != 0:
        logger('git').error(indent_lines(r.stderr, 6))
        return
    if r.stdout.strip() != 'Already up-to-date.':
        logger().info(indent_lines('Updated \'{}\'.', 6).format(repo_name))


PluginCallbacks = namedtuple('PluginCallbacks',
        ['repo_name', 'install', 'update'])


PLUGIN_CALLBACKS = {
        'github': PluginCallbacks(
            get_github_repo_name,
            install_plugin_from_github,
            update_plugin_from_github)
        }


def get_plugin_callbacks(plugin):
    try:
        return PLUGIN_CALLBACKS[plugin['type']]
    except KeyError:
        raise RuntimeError(
                'Plugin type \'{}\' not supported.'
                .format(plugin['type']))


def get_repo_name(plugin):
    repo_name_cb = get_plugin_callbacks(plugin).repo_name
    return repo_name_cb(plugin)


def install_plugin(package_name, load_type, plugin):
    install_cb = get_plugin_callbacks(plugin).install
    return install_cb(package_name, load_type, plugin)


def update_plugin(package_name, load_type, plugin):
    update_cb = get_plugin_callbacks(plugin).update
    return update_cb(package_name, load_type, plugin)


def clean_up_plugin(package_name, load_type, plugin):
    repo_name = get_repo_name(plugin)
    repo_dir = get_repo_dir(repo_name)
    plugin_dir = get_plugin_dir(package_name, load_type, repo_name)
    try:
        os.rmdir(repo_dir)
    except FileNotFoundError:
        pass
    try:
        os.unlink(plugin_dir)
    except FileNotFoundError:
        pass


def normalize_plugin_spec(plugin):
    if isinstance(plugin, str):
        plugin = {'source': plugin}
    defaults = {'type': 'github'}
    defaults.update(plugin)
    return defaults


def walk_package(package_name, conf, cb):
    ensure_dir_exists(get_package_dir(package_name))
    for idx, (load_type, plugin_list) in enumerate(conf.items(), start=1):
        logger().info(
                indent_lines('({}/{}) Directory \'{}\'', 2)
                .format(idx, len(conf), load_type))
        ensure_dir_exists(get_load_type_dir(package_name, load_type))
        for idx, p in enumerate(plugin_list, start=1):
            p = normalize_plugin_spec(p)
            logger().info(
                    indent_lines('({}/{}) Plugin \'{}\'', 4)
                    .format(idx, len(plugin_list), p['source']))
            cb(package_name, load_type, p)


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    config = read_config(get_config_file())

    ensure_dir_exists(os.path.join(WORKING_DIR, PACK_DIR_NAME))
    ensure_dir_exists(os.path.join(WORKING_DIR, REPO_DIR_NAME))

    if len(sys.argv) < 2:
        raise RuntimeError('No command specified.')

    if sys.argv[1] == 'install':
        cb = install_plugin
    elif sys.argv[1] == 'update':
        cb = update_plugin
    else:
        raise RuntimeError('Unknown command \'{}\'.'.format(sys.argv[1]))

    for idx, (pack, conf) in enumerate(config.items(), start=1):
        logger().info(
                '({}/{}) Package \'{}\''
                .format(idx, len(config), pack))
        walk_package(pack, conf, cb)

    logger().info('Running helptags.')
    r = subprocess.run(['vim', '+helptags ALL', '+quit'])
    if r.returncode != 0:
        logger('vim').error('Failed to run helptags.')
