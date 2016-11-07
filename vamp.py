#!/bin/env python3
# -*- encoding: utf-8 -*-

import os
import sys
import json
import subprocess
import multiprocessing
import shutil
import logging
from collections import namedtuple


SCRIPT_NAME = os.path.splitext(os.path.basename(sys.argv[0]))[0]
WORKING_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
PACK_DIR_NAME = 'pack'
REPO_DIR_NAME = 'repo'
CONFIG_FILE_NAME = 'vamp.json'
MARKER_FILE_NAME = '.vamp'


WORKER_COUNT = 5
work_list = None
worker_pool = None


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


def touch(path):
    with open(path, 'a+'):
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
    logger().debug('Reading config file %r.', conf_file)
    with open(conf_file, mode='r') as cf:
        return json.load(cf)


def get_github_repo_name(plugin):
    return plugin['source'].split('/')[1]


def install_github_plugin(package_name, load_type, plugin):
    repo_name = get_github_repo_name(plugin)
    repo_dir = get_repo_dir(repo_name)
    if os.path.isdir(repo_dir) and os.path.isdir(os.path.join(repo_dir, '.git')):
        logger().debug('Plugin repo %r exists.', repo_name)
    else:
        repo_url = '/'.join(['https://github.com', plugin['source']]) + '.git'
        r = subprocess.run(['git', 'clone', repo_url, repo_dir],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True)
        if r.returncode != 0:
            remove_generic_plugin(package_name, load_type, plugin)
            raise RuntimeError(r.stderr)
        marker_file = os.path.join(repo_dir, MARKER_FILE_NAME)
        touch(marker_file)

    if 'subpath' in plugin:
        ln_target = os.path.join(repo_dir, plugin['subpath'])
    else:
        ln_target = repo_dir

    ln_path = get_plugin_dir(package_name, load_type, repo_name)
    try:
        os.symlink(ln_target, ln_path, target_is_directory=True)
    except FileExistsError:
        if os.path.islink(ln_path):
            if not os.path.samefile(ln_path, ln_target):
                raise RuntimeError(
                        '{} is a symlink that points to a wrong path.'
                        .format(repr(ln_path)))
        else:
            raise RuntimeError(
                    '{} exists but is not a symlink.'
                    .format(repr(ln_path)))
    return 'Installed'


def cmd_after_cd(dir_path, cmd):
    try:
        os.chdir(dir_path)
        r = subprocess.run(cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True)
        return r
    except Exception as e:
        return e


def update_github_plugin(package_name, load_type, plugin):
    repo_name = get_github_repo_name(plugin)
    repo_dir = get_repo_dir(repo_name)
    r = cmd_after_cd(repo_dir, ['git', 'pull'])
    if isinstance(r, Exception):
        raise r
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    if r.stdout.strip() != 'Already up-to-date.':
        return 'Updated'


def remove_generic_plugin(package_name, load_type, plugin):
    repo_name = get_repo_name(plugin)
    repo_dir = get_repo_dir(repo_name)
    plugin_dir = get_plugin_dir(package_name, load_type, repo_name)
    try:
        shutil.rmtree(repo_dir)
    except FileNotFoundError:
        pass
    try:
        os.unlink(plugin_dir)
    except FileNotFoundError:
        pass
    return 'Removed'


def clean_generic_plugin(package_name, load_type, plugin):
    repo_name = get_repo_name(plugin)
    repo_dir = get_repo_dir(repo_name)
    marker_file = os.path.join(repo_dir, MARKER_FILE_NAME)
    if os.path.isdir(repo_dir) and not os.path.isfile(marker_file):
        return remove_generic_plugin(package_name, load_type, plugin)


PluginCallbacks = namedtuple('PluginCallbacks',
        ['repo_name', 'install', 'update', 'remove', 'clean'])


PLUGIN_CALLBACKS = {
        'github': PluginCallbacks(
            get_github_repo_name,
            install_github_plugin,
            update_github_plugin,
            remove_generic_plugin,
            clean_generic_plugin)
        }


def get_plugin_callbacks(plugin):
    try:
        return PLUGIN_CALLBACKS[plugin['type']]
    except KeyError:
        raise RuntimeError(
                'Plugin type {} not supported.'
                .format(repr(plugin['type'])))


def get_repo_name(plugin):
    repo_name_cb = get_plugin_callbacks(plugin).repo_name
    return repo_name_cb(plugin)


def apply_async(func, package_name, load_type, plugin):
    global work_list
    global worker_pool
    if work_list is None:
        work_list = []
    if worker_pool is None:
        worker_pool = multiprocessing.Pool(processes=WORKER_COUNT)
    work_list.append(
            worker_pool.apply_async(
                func, args=(package_name, load_type, plugin),
                callback=lambda res: async_work_success(plugin, res),
                error_callback=lambda exc: async_work_fail(plugin, exc)))


def async_work_success(plugin, result):
    if result is not None:
        logger().info('Done processing %r: %s',
                get_repo_name(plugin), str(result))
    else:
        logger().info('Done processing %r', get_repo_name(plugin))


def async_work_fail(plugin, exc):
    logger().error('Failed to process %r: %s', get_repo_name(plugin), str(exc))


def install_plugin(package_name, load_type, plugin, rest_argv):
    if len(rest_argv) == 0 or get_repo_name(plugin) in rest_argv:
        install_cb = get_plugin_callbacks(plugin).install
        apply_async(install_cb, package_name, load_type, plugin)


def update_plugin(package_name, load_type, plugin, rest_argv):
    if len(rest_argv) == 0 or get_repo_name(plugin) in rest_argv:
        update_cb = get_plugin_callbacks(plugin).update
        apply_async(update_cb, package_name, load_type, plugin)


def clean_plugin(package_name, load_type, plugin, rest_argv):
    if len(rest_argv) == 0 or get_repo_name(plugin) in rest_argv:
        clean_cb = get_plugin_callbacks(plugin).clean
        try:
            result = clean_cb(package_name, load_type, plugin)
        except Exception as e:
            async_work_fail(plugin, e)
            return
        async_work_success(plugin, result)


def remove_plugin(package_name, load_type, plugin, rest_argv):
    if len(rest_argv) == 0 or get_repo_name(plugin) in rest_argv:
        remove_cb = get_plugin_callbacks(plugin).remove
        try:
            result = remove_cb(package_name, load_type, plugin)
        except Exception as e:
            async_work_fail(plugin, e)
            return
        async_work_success(plugin, result)


def list_plugin(package_name, load_type, plugin, rest_argv):
    if len(rest_argv) == 0 or get_repo_name(plugin) in rest_argv:
        logger().info('---------------------------')
        logger().info('Type: %r', plugin['type'])
        logger().info('Source: %r', plugin['source'])
        if 'subpath' in plugin:
            logger().info('Subpath: %r', plugin['subpath'])


def normalize_plugin_spec(plugin):
    if isinstance(plugin, str):
        plugin = {'source': plugin}
    defaults = {'type': 'github'}
    defaults.update(plugin)
    return defaults


def walk_package(package_name, conf, rest_argv, cb):
    ensure_dir_exists(get_package_dir(package_name))
    for idx, (load_type, plugin_list) in enumerate(conf.items(), start=1):
        logger().debug('(%d/%d) Directory %r', idx, len(conf), load_type)
        ensure_dir_exists(get_load_type_dir(package_name, load_type))
        for idx, p in enumerate(plugin_list, start=1):
            p = normalize_plugin_spec(p)
            logger().debug('(%d/%d) Plugin %r', idx, len(plugin_list), get_repo_name(p))
            cb(package_name, load_type, p, rest_argv)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    config = read_config(get_config_file())

    ensure_dir_exists(os.path.join(WORKING_DIR, PACK_DIR_NAME))
    ensure_dir_exists(os.path.join(WORKING_DIR, REPO_DIR_NAME))

    if len(sys.argv) < 2:
        raise RuntimeError('No command specified.')

    if sys.argv[1] == 'install':
        cb = install_plugin
    elif sys.argv[1] == 'update':
        cb = update_plugin
    elif sys.argv[1] == 'remove':
        cb = remove_plugin
    elif sys.argv[1] == 'clean':
        cb = clean_plugin
    elif sys.argv[1] == 'list':
        cb = list_plugin
    else:
        raise RuntimeError('Unknown command {}.'.format(repr(sys.argv[1])))

    rest_argv = sys.argv[2:]
    for idx, (pack, conf) in enumerate(config.items(), start=1):
        logger().debug('(%d/%d) Package %r', idx, len(config), pack)
        walk_package(pack, conf, rest_argv, cb)

    if work_list is not None:
        for r in work_list:
            r.wait()

    if sys.argv[1] != 'list':
        logger().info('Running helptags.')
        r = subprocess.run(['vim', '+helptags ALL', '+quit'])
        if r.returncode != 0:
            logger('vim').error('Failed to run helptags.')
