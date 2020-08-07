#!/usr/bin/env python

import distutils
import subprocess
import shutil
import sys
import os
import glob


def configure(project):

    project.dependency(name='boost',
                       targets=['boost_system'],
                       repository='ssh://git@git.balp.io/boost.git',
                       version='master')

    target = project.export(name='bustache',
                            targets=['bustache'],
                            includes=['bustache/include'])

    target.when(osystem=['linux'], system=['boost_system'])

    target.when(osystem=['windows', 'osx'], deps=['boost'])


def mycopy(src, dst):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    if os.path.islink(src):
        linkto = os.readlink(src)
        os.symlink(linkto, dst)
    else:
        shutil.copy(src, dst)


def script(ctx):

    boost_dep = ctx.find_dep('boost')
    boost_dep_include = ctx.find_dep_cache_include(boost_dep)

    bustache_dir = ctx.make_project_path(os.path.join('bustache'))

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

    boost_option = []
    if not ctx.is_linux():
        boost_option.append('-D' + 'Boost_INCLUDE_DIR=' + boost_dep_include)

    ret = subprocess.call(['cmake', bustache_dir] + boost_option + opt_arch +
                          [opt_variant, opt_target],
                          cwd=target_dir)
    if ret:
        print "ERROR: cmake"
        return

    ret = subprocess.call(
        ['cmake', '--build', '.', '--target', 'bustache', '--config', variant],
        cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake --build")

    out_path = ctx.make_out_path()
    if os.path.exists(out_path):
        shutil.rmtree(out_path)
    os.makedirs(out_path)

    types = ('*.pdb', '*.dll', '*.lib', '*.a', '*.so', '*.so.*')
    files_grabbed = []
    for files in types:
        files_grabbed.extend(glob.glob(os.path.join(target_dir, files)))

    for file in files_grabbed:
        print(file)
        mycopy(file, out_path)
