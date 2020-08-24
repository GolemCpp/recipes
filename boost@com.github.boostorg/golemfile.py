#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import distutils
import multiprocessing
import shutil


def configure(project):

    targets = [
        'boost_atomic', 'boost_chrono', 'boost_container', 'boost_context',
        'boost_coroutine', 'boost_date_time', 'boost_fiber',
        'boost_filesystem', 'boost_graph', 'boost_iostreams', 'boost_locale',
        'boost_log_setup', 'boost_log', 'boost_math_c99f', 'boost_math_c99l',
        'boost_math_c99', 'boost_math_tr1f', 'boost_math_tr1l',
        'boost_math_tr1', 'boost_prg_exec_monitor', 'boost_program_options',
        'boost_random', 'boost_regex', 'boost_serialization', 'boost_system',
        'boost_thread', 'boost_timer', 'boost_type_erasure',
        'boost_unit_test_framework', 'boost_wave', 'boost_wserialization'
    ]

    def target_decorator(target_name, config, context):
        return target_name

    def artifacts_generator(decorated_target, config, context):
        artifacts = []
        for suffix in context.artifact_suffix(config):
            artifact = context.artifact_prefix(
                config) + decorated_target + suffix
            artifacts.append(artifact)
            if suffix == '.so':
                artifacts.append('{}.{}'.format(artifact,
                                                context.version.semver_short))
        return artifacts

    project.library(name='boost',
                    targets=targets,
                    scripts=[script],
                    target_decorators=[target_decorator],
                    artifacts_generators=[artifacts_generator])

    project.export(name='boost',
                   includes=['include'],
                   defines=[
                       'BOOST_ASIO_DISABLE_THREAD_KEYWORD_EXTENSION',
                       'BOOST_AUTO_LINK_NOMANGLE'
                   ],
                   licenses='LICENSE_1_0.txt')

    # NOTE: Not available on Windows
    # 'boost_signals'

    # NOTE: Static linking only
    # 'boost_exception'
    # 'boost_test_exec_monitor'


def make_install_path(ctx):
    out_path = ctx.make_out_path()
    install_folder = os.path.basename(out_path) + "-install"
    prefix_dir = os.path.join(os.path.dirname(out_path), install_folder)
    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir)
    return prefix_dir


def script(ctx):

    boost_dir = ctx.get_project_dir()
    target_dir = ctx.context.out_dir

    bootstrap_opt_libs = []
    bootstrap_opt_libs.append('--without-libraries=python')

    msvc_cmd = ''
    if ctx.is_windows():
        msvc_cmd = ctx.msvc_vcvars_cmd()

    bootstrap_bin = 'bootstrap.bat' if ctx.is_windows() else './bootstrap.sh'

    cmd = msvc_cmd + ' '.join([bootstrap_bin] + bootstrap_opt_libs)

    if ctx.is_windows():
        cmd = 'cmd /V /C "{}"'.format(cmd)

    print("Run command: {}".format(cmd))
    ret = subprocess.call(cmd, cwd=boost_dir, shell=True)
    if ret:
        raise RuntimeError("ERROR: " + bootstrap_bin)

    boost_build_dir = os.path.join(target_dir, 'boost-build')
    boost_stage_dir = os.path.join(target_dir, 'boost-stage')

    if os.path.exists(boost_build_dir):
        shutil.rmtree(boost_build_dir)

    if os.path.exists(boost_stage_dir):
        shutil.rmtree(boost_stage_dir)

    opt_dirs = [
        '--build-dir=' + boost_build_dir, '--stagedir=' + boost_stage_dir
    ]

    opt_variant = 'variant='
    if ctx.is_debug():
        opt_variant += 'debug'
    else:
        opt_variant += 'release'

    opt_arch = 'address-model='
    if ctx.is_x64():
        opt_arch += '64'
    else:
        opt_arch += '32'

    opt_runtime = 'runtime-link=' + ctx.runtime()
    opt_link = 'link=' + ctx.link()

    opt_libs = []
    opt_libs.append('--without-python')

    opt_headers = []
    if not ctx.is_windows():
        opt_headers = ['headers']

    if ctx.is_windows():
        msvc_cmd += 'set "VS150COMNTOOLS=!VS160COMNTOOLS!" && '  # workaround

    prefix_dir = make_install_path(ctx)

    b2_bin = 'b2' if ctx.is_windows() else './b2'
    cmd = msvc_cmd + ' '.join([
        b2_bin, '-a', '-j' +
        str(multiprocessing.cpu_count()), '--layout=system',
        'define=BOOST_ASIO_DISABLE_THREAD_KEYWORD_EXTENSION', opt_variant,
        opt_arch, opt_runtime, opt_link
    ] + opt_dirs + opt_libs + ['install', '--prefix=' + prefix_dir])

    if ctx.is_windows():
        cmd = 'cmd /V /C "{}"'.format(cmd)

    print("Run command: {}".format(cmd))
    ret = subprocess.call(cmd, cwd=boost_dir, shell=True)
    if ret:
        raise RuntimeError("ERROR: b2")

    out_path = ctx.make_out_path()
    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'lib'),
                                 out_path,
                                 preserve_symlinks=1)

    distutils.dir_util.copy_tree(os.path.join(prefix_dir, 'include', 'boost'),
                                 os.path.join(boost_dir, 'include', 'boost'))

    if os.path.exists(boost_build_dir):
        shutil.rmtree(boost_build_dir)

    if os.path.exists(boost_stage_dir):
        shutil.rmtree(boost_stage_dir)