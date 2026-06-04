#!/usr/bin/env python


def configure(project):

    target = project.export(name='sdl2',
                            includes=[os.path.join('SDL2', 'include')])

    target.when(variant='debug', targets=['SDL2d'])
    target.when(variant='release', targets=['SDL2'])


import os
import sys
import glob
import shutil
import subprocess
import urllib2
import zipfile


def download_latest_src(ctx):
    sdl2_dir = ctx.make_project_path('SDL2')

    name = 'SDL2-2.0.10'

    downloadURL = "https://www.libsdl.org/release/" + name + ".zip"

    print "Downloading ", downloadURL
    response = urllib2.urlopen(downloadURL)
    zippedData = response.read()

    # save data to memory
    from StringIO import StringIO
    zipdata = StringIO()
    zipdata.write(zippedData)

    # extract the data
    with zipfile.ZipFile(zipdata) as z:
        z.extractall(sdl2_dir)

    for filename in os.listdir(os.path.join(sdl2_dir, name)):
        shutil.move(os.path.join(sdl2_dir, name, filename),
                    os.path.join(sdl2_dir, filename))


def script(ctx):

    sdl2_dir = ctx.make_project_path('SDL2')

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if not os.path.exists(sdl2_dir):
        download_latest_src(ctx)

    variant_name = ''
    if ctx.is_debug():
        variant_name += 'Debug'
    else:
        variant_name += 'Release'

    opt_variant = '-DCMAKE_BUILD_TYPE:STRING=' + variant_name

    opt_link_shared = '-DSDL_SHARED:BOOL='
    opt_link_static = '-DSDL_STATIC:BOOL='
    if ctx.is_static():
        opt_link_shared += 'OFF'
        opt_link_static += 'ON'
    else:
        opt_link_shared += 'ON'
        opt_link_static += 'OFF'
    opt_link = [opt_link_shared, opt_link_static]

    opt_runtime_link = '-DFORCE_STATIC_VCRT:BOOL='
    if ctx.runtime_link() == ctx.link_shared():
        opt_runtime_link += 'OFF'
    else:
        opt_runtime_link += 'ON'

    opt_arch = ['-A']
    if ctx.is_x64():
        opt_arch.append('x64')
    else:
        opt_arch.append('x86')

    print ' '.join(['cmake', sdl2_dir] + opt_arch +
                   [opt_variant, opt_runtime_link] + opt_link)
    ret = subprocess.call(['cmake', sdl2_dir] + opt_arch +
                          [opt_variant, opt_runtime_link] + opt_link +
                          ['-DEXTRA_LIBS=vcruntime'],
                          cwd=target_dir)
    if ret:
        print "ERROR: cmake"
        return 1

    ret = subprocess.call(['cmake', '--build', '.', '--config', variant_name],
                          cwd=target_dir)
    if ret:
        print "ERROR: cmake --build"
        return 1

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(
        os.path.join(target_dir, variant_name), out_path)

    include_src = os.path.join(sdl2_dir, 'include')
    include_dest = os.path.join(sdl2_dir, 'include', 'SDL2')
    for filename in os.listdir(include_src):
        if not os.path.exists(include_dest):
            os.makedirs(include_dest)
        shutil.move(os.path.join(include_src, filename),
                    os.path.join(include_dest, filename))
