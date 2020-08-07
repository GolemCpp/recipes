#!/usr/bin/env python

import distutils
import subprocess
import shutil
import glob
import sys
import os


def configure(project):

    target = project.library(name='mongocxx', scripts=[script])

    target.when(link=['shared'],
                targets=['bson-1.0', 'mongoc-1.0', 'bsoncxx', 'mongocxx'])

    target.when(link=['static'],
                targets=[
                    'mongocxx-static', 'bsoncxx-static', 'mongoc-static-1.0',
                    'bson-static-1.0'
                ])

    target = project.export(name='mongocxx', includes=['include'])

    target.when(link=['shared'],
                targets=['bson-1.0', 'mongoc-1.0', 'bsoncxx', 'mongocxx'])

    target.when(link=['static'],
                targets=[
                    'mongocxx-static', 'bsoncxx-static', 'mongoc-static-1.0',
                    'bson-static-1.0'
                ])
    target.when(link=['static'],
                defines=[
                    'MONGOCXX_STATIC', 'BSONCXX_STATIC', 'MONGOC_STATIC',
                    'BSON_STATIC'
                ])

    target.when(link=['static'],
                osystem=['linux'],
                lib=["rt", "sasl2", "icuuc", "z", "resolv"])

    target.when(link=['static'],
                osystem=['osx'],
                lib=["sasl2", "z", "resolv"],
                framework=['CoreFoundation', 'Security'])


def build_mongoc(ctx):

    mongoc_dir = ctx.get_project_dir()

    target_dir = os.path.join(ctx.context.out_dir, 'mongoc')
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

    prefix_dir = os.path.join(ctx.context.out_dir, 'install')
    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir)

    prefix_path = '-DCMAKE_INSTALL_PREFIX=' + prefix_dir

    ret = subprocess.call(['cmake', mongoc_dir] + opt_arch + [
        opt_variant, opt_target, '-DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF',
        '-DENABLE_EXAMPLES=OFF', '-DENABLE_TESTS=OFF', prefix_path
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


def build_mongocxx(ctx):

    mongocxx_dir = ctx.make_project_path('mongo-cxx-driver')

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

    opt_arch = ['-A']
    if ctx.is_x64():
        opt_arch.append('x64')
    else:
        opt_arch.append('x86')

    if not ctx.is_windows():
        opt_arch = []

    prefix_dir = os.path.join(ctx.context.out_dir, 'install')
    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir)

    prefix_path = '-DCMAKE_INSTALL_PREFIX=' + prefix_dir

    prefix_path_bis = '-DCMAKE_PREFIX_PATH=' + prefix_dir

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


def mycopy(src, dst):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    if os.path.islink(src):
        linkto = os.readlink(src)
        os.symlink(linkto, dst)
    else:
        shutil.copy(src, dst)


def script(ctx):

    build_mongoc(ctx)
    build_mongocxx(ctx)

    out_path = ctx.make_out_path()

    prefix_dir = os.path.join(ctx.context.out_dir, 'install')

    types = ('*.pdb', '*.dll', '*.lib', '*.dylib*', '*.so*', '*.a*')
    files_grabbed = []
    for files in types:
        files_grabbed.extend(glob.glob(os.path.join(prefix_dir, 'lib', files)))

    for file in files_grabbed:
        print(file)
        mycopy(file, out_path)

    include_dir = ctx.make_project_path('include')
    os.makedirs(include_dir)

    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'include', 'bsoncxx',
                                              'v_noabi', 'bsoncxx'),
                                 os.path.join(include_dir, 'bsoncxx'),
                                 preserve_symlinks=1)

    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'include',
                                              'mongocxx', 'v_noabi',
                                              'mongocxx'),
                                 os.path.join(include_dir, 'mongocxx'),
                                 preserve_symlinks=1)

    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'include',
                                              'libbson-1.0', 'bson'),
                                 os.path.join(include_dir, 'bson'),
                                 preserve_symlinks=1)

    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'include',
                                              'libmongoc-1.0', 'mongoc'),
                                 os.path.join(include_dir, 'mongoc'),
                                 preserve_symlinks=1)
