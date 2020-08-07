#!/usr/bin/env python

import distutils
import subprocess
import shutil
import glob
import sys
import os


def configure(project):
    def artifacts_generator(decorated_target, config, context):
        artifacts = []
        for suffix in context.artifact_suffix(config):
            artifact = context.artifact_prefix(
                config) + decorated_target + suffix
            artifacts.append(artifact)
            if suffix == '.so':
                artifacts.append('{}.{}.{}'.format(artifact,
                                                   context.version.major,
                                                   context.version.minor))
        return artifacts

    project.library(name='openssl',
                    targets=['crypto', 'ssl'],
                    scripts=[script],
                    artifacts_generators=[artifacts_generator])

    project.export(name='openssl',
                   includes=['output/include'],
                   licenses=['LICENSE'])


def script(ctx):

    openssl_dir = ctx.get_project_dir()

    openssl_config = []
    if ctx.is_windows() or ctx.is_darwin():
        openssl_config.append('perl')
        openssl_config.append('Configure')
    else:
        openssl_config.append('./config')

    openssl_make = []
    if ctx.is_windows():
        openssl_make.append('nmake')
    else:
        openssl_make.append('make')

    opt_variant = ''
    if ctx.is_debug():
        opt_variant = '--debug'
        if ctx.is_windows():
            if ctx.is_x64():
                openssl_config.append('debug-VC-WIN64A')
            else:
                openssl_config.append('debug-VC-WIN32')
        elif ctx.is_darwin():
            if ctx.is_x64():
                openssl_config.append('debug-darwin64-x86_64-cc')
            else:
                openssl_config.append('debug-darwin-i386-cc')
    else:
        opt_variant = '--release'
        if ctx.is_windows():
            if ctx.is_x64():
                openssl_config.append('VC-WIN64A')
            else:
                openssl_config.append('VC-WIN32')
        elif ctx.is_darwin():
            if ctx.is_x64():
                openssl_config.append('darwin64-x86_64-cc')
            else:
                openssl_config.append('darwin-i386-cc')

    opt_libs = []
    opt_libs.append('--prefix=' + os.path.join(openssl_dir, 'output'))
    opt_libs.append('--openssldir=' + os.path.join(openssl_dir, 'output'))

    openssl_config_args = ['no-asm', 'enable-static-engine', opt_variant]

    if ctx.is_static():
        openssl_config_args.append('no-shared')

    if ctx.is_windows():
        cmd = [
            'cmd', '/c', 'vswhere', '-latest', '-products', '*', '-property',
            'installationPath'
        ]
        print(' '.join(cmd))
        ret = subprocess.Popen(
            cmd,
            cwd='C:\\Program Files (x86)\\Microsoft Visual Studio\\Installer',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = ret.communicate()
        if ret.returncode:
            print("ERROR: " + ' '.join(cmd))
            return -1
        lines = out.splitlines()
        if not lines[0]:
            return 1
        msvc_path = lines[0]
        print(msvc_path)

    cmd = openssl_config + openssl_config_args + opt_libs
    print(' '.join(cmd))

    my_env = os.environ

    if ctx.is_windows():
        my_env['PATH'] = 'C:\\Strawberry\\perl\\bin;' + my_env['PATH']

    configure_cmd = cmd
    if ctx.is_windows():
        configure_cmd = ' '.join(cmd)
    if subprocess.call(configure_cmd, cwd=openssl_dir, env=my_env):
        print("ERROR: Can't configure")
        return 1

    call_msvc = []
    if ctx.is_windows():
        vcvars = msvc_path + '\\VC\\Auxiliary\\Build\\vcvarsall.bat'
        call_msvc = [
            'call', '"' + vcvars + '"', ctx.context.env['MSVC_TARGETS'][0],
            '&&'
        ]
        print(call_msvc)

    cmd = call_msvc + openssl_make
    print(' '.join(cmd))

    build_cmd = cmd
    if ctx.is_windows():
        build_cmd = ' '.join(cmd)
    if subprocess.call(build_cmd, cwd=openssl_dir, shell=True):
        print("ERROR: Can't build")
        return 1

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts(openssl_dir, out_path)

    distutils.dir_util.copy_tree(
        os.path.join(openssl_dir, 'include', 'openssl'),
        os.path.join(openssl_dir, 'output', 'include', 'openssl'))
