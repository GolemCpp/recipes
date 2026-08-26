#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import shutil
import glob
import sys
import os


def configure(project):
    def shared_targets_decorator(target_name, config, context):
        return target_name

    def static_targets_decorator(target_name, config, context):
        return target_name + '-static'

    def artifacts_generator(decorated_target, config, context):
        artifacts = []
        for suffix in context.artifact_suffix(config):
            artifact = context.artifact_prefix(
                config) + decorated_target + suffix
            artifacts.append(artifact)
            if suffix == '.so':
                artifacts.append('{}.{}'.format(artifact, '_noabi'))
                artifacts.append('{}.{}.{}.{}'.format(artifact,
                                                      context.version.major,
                                                      context.version.minor,
                                                      context.version.patch))
        return artifacts

    project.dependency(
        name='mongo-c-driver',
        repository='https://github.com/mongodb/mongo-c-driver.git',
        version='~1.17.0',
        variant='release')

    target = project.library(name='mongo-cxx-driver',
                             targets=['bsoncxx', 'mongocxx'],
                             scripts=[script],
                             artifacts_generators=[artifacts_generator],
                             deps=['mongo-c-driver'])

    target.when(link=['shared'], target_decorators=[shared_targets_decorator])
    target.when(link=['static'], target_decorators=[static_targets_decorator])

    target = project.export(name='mongo-cxx-driver',
                            includes=['include'],
                            licenses=['LICENSE', 'THIRD-PARTY-NOTICES'],
                            deps=['mongo-c-driver'])

    target.when(link=['static'], defines=['MONGOCXX_STATIC', 'BSONCXX_STATIC'])


def make_install_path(ctx):
    out_path = ctx.make_out_path()
    install_folder = os.path.basename(out_path) + "-install"
    prefix_dir = os.path.join(os.path.dirname(out_path), install_folder)
    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir)
    return prefix_dir


def make_cmake_prefix(ctx):
    mongoc_out_path = ctx.find_dependency_libraries('mongo-c-driver')[0]
    install_folder = os.path.basename(mongoc_out_path) + "-install"
    prefix_dir = os.path.join(os.path.dirname(mongoc_out_path), install_folder)
    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir)
    return prefix_dir


def build_mongocxx(ctx):

    mongocxx_dir = ctx.get_project_dir()

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    variant = None
    if ctx.is_debug():
        variant = 'Debug'
    else:
        variant = 'Release'

    opt_variant = '-DCMAKE_BUILD_TYPE=' + variant

    opt_target = '-DBUILD_SHARED_LIBS='
    if ctx.is_static():
        opt_target += 'OFF'
    else:
        opt_target += 'ON'

    opt_arch = ['-A', ctx.vs_platform()] if ctx.is_windows() else []

    prefix_dir = make_install_path(ctx)
    mongoc_out_path = make_cmake_prefix(ctx)

    prefix_path = '-DCMAKE_INSTALL_PREFIX=' + prefix_dir

    prefix_path_bis = '-DCMAKE_PREFIX_PATH=' + mongoc_out_path

    ret = subprocess.call(['cmake', mongocxx_dir] + opt_arch + [
        opt_variant, opt_target, '-DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF',
        '-DENABLE_EXAMPLES=OFF', '-DENABLE_TESTS=OFF', prefix_path_bis,
        prefix_path
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

    build_mongocxx(ctx)

    prefix_dir = make_install_path(ctx)

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(os.path.join(prefix_dir, 'lib'),
                                         out_path)

    include_dir = ctx.make_project_path('include')
    os.makedirs(include_dir)

    shutil.copytree(os.path.join(prefix_dir, 'include', 'bsoncxx', 'v_noabi', 'bsoncxx'),
                    os.path.join(include_dir, 'bsoncxx'),
                    dirs_exist_ok=True,
                    symlinks=True)

    shutil.copytree(os.path.join(prefix_dir, 'include', 'mongocxx', 'v_noabi', 'mongocxx'),
                    os.path.join(include_dir, 'mongocxx'),
                    dirs_exist_ok=True,
                    symlinks=True)
