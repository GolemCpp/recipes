#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import distutils
import subprocess
import shutil
import glob
import sys
import os


def configure(project):
    def shared_targets_decorator(target_name, config, context):
        return target_name + '-1.0'

    def static_targets_decorator(target_name, config, context):
        return target_name + '-static-1.0'

    def artifacts_generator(decorated_target, config, context):
        artifacts = []
        for suffix in context.artifact_suffix(config):
            artifact = context.artifact_prefix(
                config) + decorated_target + suffix
            artifacts.append(artifact)
            if suffix == '.so':
                artifacts.append('{}.{}'.format(artifact, 0))
                artifacts.append('{}.{}.{}.{}'.format(artifact, 0, 0, 0))
        return artifacts

    project.dependency(name='zlib',
                       repository='https://github.com/madler/zlib.git',
                       version='~1.2.11',
                       variant="release",
                       shallow=True)

    project.dependency(name='openssl',
                       repository='https://github.com/openssl/openssl.git',
                       version='~1.1.1',
                       variant="release",
                       shallow=True)

    target = project.library(name='mongo-c-driver',
                             targets=['bson', 'mongoc'],
                             deps=['zlib', 'openssl'],
                             scripts=[script],
                             artifacts_generators=[artifacts_generator])

    target.when(link=['shared'], target_decorators=[shared_targets_decorator])
    target.when(link=['static'], target_decorators=[static_targets_decorator])

    target = project.export(name='mongo-c-driver',
                            includes=['include'],
                            licenses=['COPYING', 'THIRD_PARTY_NOTICES'])

    target.when(link=['static'], defines=['MONGOC_STATIC', 'BSON_STATIC'])

    target.when(link=['static'],
                osystem=['linux'],
                lib=["rt", "sasl2", "icuuc", "z", "resolv"])

    target.when(link=['static'],
                osystem=['osx'],
                lib=["sasl2", "z", "resolv"],
                framework=['CoreFoundation', 'Security'])


def make_install_path(ctx):
    out_path = ctx.make_out_path()
    install_folder = os.path.basename(out_path) + "-install"
    prefix_dir = os.path.join(os.path.dirname(out_path), install_folder)
    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir)
    return prefix_dir


def build_mongoc(ctx):

    mongoc_dir = ctx.get_project_dir()

    version_file = open(os.path.join(mongoc_dir, 'VERSION_CURRENT'), 'w')
    ret = subprocess.call(['python', 'build/calc_release_version.py'],
                          stdout=version_file,
                          cwd=mongoc_dir)
    if ret:
        raise RuntimeError("Cannot calculate current version")

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    variant = None
    if ctx.is_debug():
        variant = 'Debug'
    else:
        variant = 'Release'

    opt_variant = '-DCMAKE_BUILD_TYPE=' + variant

    opt_target = '-DENABLE_STATIC='
    if ctx.is_static():
        opt_target += 'ON'
    else:
        opt_target += 'OFF'

    opt_arch = ['-A']
    if ctx.is_x64():
        opt_arch.append('x64')
    else:
        opt_arch.append('x86')

    if not ctx.is_windows():
        opt_arch = []

    prefix_dir = make_install_path(ctx)

    prefix_path = '-DCMAKE_INSTALL_PREFIX=' + prefix_dir

    zlib_libs = ctx.find_dependency_libraries_files(dep_name='zlib',
                                                    target_name='z')
    crypto_libs = ctx.find_dependency_libraries_files(dep_name='openssl',
                                                      target_name='crypto')
    ssl_libs = ctx.find_dependency_libraries_files(dep_name='openssl',
                                                   target_name='ssl')

    ret = subprocess.call(['cmake', mongoc_dir] + opt_arch + [
        opt_variant, opt_target, '-DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF',
        '-DENABLE_EXAMPLES=OFF', '-DENABLE_TESTS=OFF',
        '-DZLIB_LIBRARY=' + zlib_libs[0],
        '-DZLIB_INCLUDE_DIR=' + ctx.find_dependency_includes('zlib')[0],
        '-DOPENSSL_CRYPTO_LIBRARY=' + crypto_libs[0],
        '-DOPENSSL_SSL_LIBRARY=' + ssl_libs[0], '-DOPENSSL_INCLUDE_DIR=' +
        ctx.find_dependency_includes('openssl')[0], prefix_path
    ],
                          cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake")

    ret = subprocess.call(['cmake', '--build', '.', '--config', variant],
                          cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake --build")

    ret = subprocess.call(['make', 'install'], cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: make install")


def script(ctx):

    build_mongoc(ctx)

    prefix_dir = make_install_path(ctx)

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts(os.path.join(prefix_dir, 'lib'), out_path)

    include_dir = ctx.make_project_path('include')
    os.makedirs(include_dir)

    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'include',
                                              'libbson-1.0', 'bson'),
                                 os.path.join(include_dir, 'bson'),
                                 preserve_symlinks=1)

    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'include',
                                              'libmongoc-1.0', 'mongoc'),
                                 os.path.join(include_dir, 'mongoc'),
                                 preserve_symlinks=1)
