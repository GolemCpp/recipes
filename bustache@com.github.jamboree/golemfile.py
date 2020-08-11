#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import distutils
import subprocess
import shutil
import sys
import os
import glob


def configure(project):

    project.dependency(name='boost',
                       targets=["boost_system"],
                       repository='https://github.com/boostorg/boost.git',
                       version='~1.69.0',
                       variant='release',
                       shallow=True)

    project.library(name='bustache', scripts=[script], deps=['boost'])

    project.export(name='bustache',
                   includes=['include'],
                   deps=['boost'],
                   licenses=['README.md'])


def script(ctx):

    bustache_dir = ctx.get_project_dir()

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
        opt_target += '0'
    else:
        opt_target += '1'

    opt_arch = []
    if ctx.is_windows():
        opt_arch = ['-A']
        if ctx.is_x64():
            opt_arch.append('x64')
        else:
            opt_arch.append('x86')

    boost_options = [
        '-DBOOST_LIBRARYDIR=' + ctx.find_dependency_libraries('boost')[0],
        '-DBOOST_INCLUDEDIR=' + ctx.find_dependency_includes('boost')[0],
        '-DBoost_NO_SYSTEM_PATHS=ON'
    ]

    ret = subprocess.call(['cmake', bustache_dir] + boost_options + opt_arch +
                          [opt_variant, opt_target],
                          cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake")

    ret = subprocess.call(
        ['cmake', '--build', '.', '--target', 'bustache', '--config', variant],
        cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake --build")

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts(target_dir, out_path)
