#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import distutils
import multiprocessing


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


def script(ctx):

    boost_dir = ctx.get_project_dir()

    bootstrap_bin = 'bootstrap.bat' if ctx.is_windows() else './bootstrap.sh'

    ret = subprocess.call([bootstrap_bin], cwd=boost_dir, shell=True)
    if ret:
        raise RuntimeError("ERROR: " + bootstrap_bin)

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
    opt_libs.append('--with-system')
    opt_libs.append('--with-atomic')
    opt_libs.append('--with-chrono')
    opt_libs.append('--with-container')
    opt_libs.append('--with-context')
    opt_libs.append('--with-coroutine')
    opt_libs.append('--with-date_time')
    opt_libs.append('--with-exception')
    opt_libs.append('--with-fiber')
    opt_libs.append('--with-filesystem')
    opt_libs.append('--with-graph')
    opt_libs.append('--with-graph_parallel')
    opt_libs.append('--with-iostreams')
    opt_libs.append('--with-locale')
    opt_libs.append('--with-log')
    opt_libs.append('--with-math')
    opt_libs.append('--with-mpi')
    opt_libs.append('--with-program_options')
    #	opt_libs.append('--with-python')
    opt_libs.append('--with-random')
    opt_libs.append('--with-regex')
    opt_libs.append('--with-serialization')
    if not ctx.is_windows():
        opt_libs.append('--with-signals')
    opt_libs.append('--with-stacktrace')
    opt_libs.append('--with-system')
    opt_libs.append('--with-test')
    opt_libs.append('--with-thread')
    opt_libs.append('--with-timer')
    opt_libs.append('--with-type_erasure')
    opt_libs.append('--with-wave')

    opt_headers = []
    if not ctx.is_windows():
        opt_headers = ['headers']

    b2_bin = 'b2' if ctx.is_windows() else './b2'
    ret = subprocess.call([
        b2_bin, '-j' + str(multiprocessing.cpu_count()), '--layout=system',
        'define=BOOST_ASIO_DISABLE_THREAD_KEYWORD_EXTENSION', opt_variant,
        opt_arch, opt_runtime, opt_link
    ] + opt_libs + opt_headers,
                          cwd=boost_dir,
                          shell=True)
    if ret:
        raise RuntimeError("ERROR: b2")

    out_path = ctx.make_out_path()
    distutils.dir_util.copy_tree(os.path.join(boost_dir, 'stage', 'lib'),
                                 out_path,
                                 preserve_symlinks=1)

    if ctx.is_windows():
        ret = subprocess.call([b2_bin, 'headers'], cwd=boost_dir, shell=True)
        if ret:
            raise RuntimeError("ERROR: b2 headers")

    distutils.dir_util.copy_tree(os.path.join(boost_dir, 'boost'),
                                 os.path.join(boost_dir, 'include', 'boost'))
