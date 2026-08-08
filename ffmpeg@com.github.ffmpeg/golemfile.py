#!/usr/bin/env python


def configure(project):

    target = project.export(name='ffmpeg',
                            targets=[
                                'avcodec', 'avdevice', 'avfilter', 'avformat',
                                'avresample', 'avutil', 'swresample', 'swscale'
                            ],
                            includes=['FFmpeg/output/include'])

    target.when(osystem=['windows'],
                dlls=[
                    'avcodec-57', 'avdevice-57', 'avfilter-6', 'avformat-57',
                    'avresample-3', 'avutil-55', 'swresample-2', 'swscale-4'
                ])


import os
import sys
import glob
import shutil
import subprocess
from golemcpp.golem import helpers


def msvc_vcvars_cmd(ctx):
    cmd = [
        'cmd', '/c', 'vswhere', '-latest', '-products', '*', '-property',
        'installationPath'
    ]
    print ' '.join(cmd)
    ret = subprocess.Popen(
        cmd,
        cwd='C:\\Program Files (x86)\\Microsoft Visual Studio\\Installer',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = ret.communicate()
    if ret.returncode:
        print "ERROR: " + ' '.join(cmd)
        return -1
    lines = out.splitlines()
    if not lines[0]:
        return 1
    msvc_path = lines[0]
    print msvc_path

    vcvars = msvc_path + '\\VC\\Auxiliary\\Build\\vcvarsall.bat'
    call_msvc = 'call "' + vcvars + '" ' + \
        ctx.context.env['MSVC_TARGETS'][0] + ' && '
    print call_msvc
    return call_msvc


def script(ctx):

    helpers.try_git(['reset', '--hard'], cwd=ctx.get_project_dir())
    helpers.try_git(['clean', '-fxd'], cwd=ctx.get_project_dir())

    ffmpeg_dir = ctx.make_project_path('FFmpeg')

    opt_variant = []
    if ctx.is_debug():
        opt_variant.append('--extra-cflags="-MDd"')
        opt_variant.append('--extra-ldflags="/NODEFAULTLIB:libcmt"')
        opt_variant.append('--enable-debug')

    opt_libs = [
        '--disable-yasm', '--disable-programs', '--disable-doc',
        '--enable-avresample', '--enable-version3', '--prefix=output'
    ]

    opt_link = []
    if ctx.is_shared():
        opt_link.append('--enable-shared')
        opt_link.append('--disable-static')
    else:
        opt_link.append('--disable-shared')
        opt_link.append('--enable-static')

    opt_platform = []
    if ctx.is_windows():
        opt_platform.append('--toolchain=msvc')

    opt_arch = []
    if ctx.is_x64():
        opt_arch.append('--arch=amd64')
    else:
        opt_arch.append('--arch=i386')

    call_msvc = msvc_vcvars_cmd(ctx)

    cmd = ' '.join(['./configure'] + opt_arch + opt_link + opt_variant +
                   opt_platform + opt_libs)
    print cmd
    my_env = os.environ
    my_env['PATH'] = 'C:\WINDOWS\System32;C:\\msys64\\usr\\bin'

    if subprocess.call("pacman -S diffutils make --noconfirm",
                       cwd=ffmpeg_dir,
                       shell=True,
                       env=my_env):
        return 1

    if subprocess.call(call_msvc + "bash -c \"" + cmd + "\"",
                       cwd=ffmpeg_dir,
                       shell=True,
                       env=my_env):
        return 1

    if subprocess.call(call_msvc + "bash -c \"make\"",
                       cwd=ffmpeg_dir,
                       shell=True,
                       env=my_env):
        return 1

    if subprocess.call(call_msvc + "bash -c \"make install\"",
                       cwd=ffmpeg_dir,
                       shell=True,
                       env=my_env):
        return 1

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(
        os.path.join(ffmpeg_dir, 'output', 'bin'), out_path)
