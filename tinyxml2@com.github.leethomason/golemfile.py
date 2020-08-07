#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess


def configure(project):

    target = project.library(name='tinyxml2', scripts=[script])

    target.when(variant='debug', targets=['tinyxml2d'])
    target.when(variant='release', targets=['tinyxml2'])

    target = project.export(name='tinyxml2',
                            includes=['include'],
                            licenses=['LICENSE.txt'])


def script(ctx):

    src_dir = ctx.get_project_dir()

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    variant = None
    if ctx.is_debug():
        variant = 'Debug'
    else:
        variant = 'Release'

    opt_variant = '-DCMAKE_BUILD_TYPE=' + variant

    opt_target_shared = '-DBUILD_SHARED_LIBS:BOOL='
    if ctx.is_static():
        opt_target_shared += 'OFF'
    else:
        opt_target_shared += 'ON'

    opt_target_static = '-DBUILD_STATIC_LIBS:BOOL='
    if ctx.is_static():
        opt_target_static += 'ON'
    else:
        opt_target_static += 'OFF'

    opt_target = [opt_target_shared, opt_target_static]

    if ctx.is_windows():
        opt_arch = ['-A']
        if ctx.is_x64():
            opt_arch.append('x64')
        else:
            opt_arch.append('x86')
    else:
        opt_arch = []

    ret = subprocess.call(['cmake', src_dir] + opt_arch +
                          [opt_variant, '-DBUILD_TESTS:BOOL=OFF'] + opt_target,
                          cwd=target_dir)
    if ret:
        print("ERROR: cmake")
        return

    ret = subprocess.call(['cmake', '--build', '.', '--config', variant],
                          cwd=target_dir)
    if ret:
        print("ERROR: cmake --build")
        return

    out_path = ctx.make_out_path()
    if ctx.is_windows():
        ctx.copy_binary_artifacts(os.path.join(target_dir, variant), out_path)
    else:
        ctx.copy_binary_artifacts(os.path.join(target_dir), out_path)

    include_dir = os.path.join(src_dir, 'include')
    if not os.path.exists(include_dir):
        os.makedirs(include_dir)
    shutil.copy2(os.path.join(src_dir, 'tinyxml2.h'), include_dir)
