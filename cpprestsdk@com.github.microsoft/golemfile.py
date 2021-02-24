#!/usr/bin/env python3


def configure(project):

    project.dependency(name='zlib',
                       repository='https://github.com/madler/zlib.git',
                       version='~1.2.11',
                       variant="release",
                       shallow=True)

    project.dependency(name='boost',
                       targets=[
                           "boost_system", "boost_filesystem", "boost_locale",
                           "boost_chrono", "boost_thread", "boost_random",
                           "boost_atomic", "boost_date_time", "boost_regex"
                       ],
                       repository='https://github.com/boostorg/boost.git',
                       version='~1.69.0',
                       variant='release',
                       shallow=True)

    project.dependency(name='openssl',
                       repository='https://github.com/openssl/openssl.git',
                       version='~1.1.1',
                       variant="release",
                       shallow=True)

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
            elif suffix == '.dylib':
                basename_prefix = context.artifact_prefix(
                    config) + decorated_target
                artifacts.append('{}.{}.{}.dylib'.format(
                    basename_prefix, context.version.major,
                    context.version.minor))
        return artifacts

    project.library(name='cpprest',
                    deps=['boost', 'openssl', 'zlib'],
                    scripts=[script],
                    artifacts_generators=[artifacts_generator])

    project.export(name='cpprest',
                   includes=['Release/include'],
                   licenses=['license.txt', 'ThirdPartyNotices.txt'],
                   deps=['boost', 'openssl', 'zlib'])


import os
import sys
import shutil
import subprocess
import distutils


def script(ctx):

    cpprest_dir = ctx.make_project_path('Release')

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

    if ctx.is_windows():
        opt_arch = ['-A']
        if ctx.is_x64():
            opt_arch.append('x64')
        else:
            opt_arch.append('x86')
    else:
        opt_arch = []

    opt_deps = []

    zlib_libs = ctx.find_dependency_libraries_files(dep_name='zlib',
                                                    target_name='z')
    crypto_libs = ctx.find_dependency_libraries_files(dep_name='openssl',
                                                      target_name='crypto')
    ssl_libs = ctx.find_dependency_libraries_files(dep_name='openssl',
                                                   target_name='ssl')
    ssl_libraries = ssl_libs[0] + ";" + crypto_libs[0]

    opt_deps += [
        '-DBOOST_LIBRARYDIR=' + ctx.find_dependency_libraries('boost')[0],
        '-DBOOST_INCLUDEDIR=' + ctx.find_dependency_includes('boost')[0],
        '-DBoost_NO_SYSTEM_PATHS=ON', '-DZLIB_LIBRARY=' + zlib_libs[0],
        '-DZLIB_INCLUDE_DIR=' + ctx.find_dependency_includes('zlib')[0],
        '-DOPENSSL_LIBRARIES=' + ssl_libraries,
        '-DOPENSSL_ROOT_DIR=' + ctx.find_dependency_libraries('openssl')[0],
        '-DOPENSSL_CRYPTO_LIBRARY=' + crypto_libs[0],
        '-DOPENSSL_SSL_LIBRARY=' + ssl_libs[0],
        '-DOPENSSL_INCLUDE_DIR=' + ctx.find_dependency_includes('openssl')[0],
        '-DWERROR=OFF'
    ]

    command = ['cmake', cpprest_dir] + opt_arch + [
        opt_variant, opt_target, '-DCPPREST_EXCLUDE_WEBSOCKETS=1',
        '-DCPPREST_ABI_TAG='
    ] + opt_deps

    print(' '.join(command))

    ret = subprocess.call(command, cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake")

    ret = subprocess.call(
        ['cmake', '--build', '.', '--target', 'cpprest', '--config', variant],
        cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake --build")

    out_path = ctx.make_out_path()

    binaries_directory = os.path.join(ctx.context.out_dir, 'Binaries')

    if ctx.is_windows():
        binaries_directory = os.path.join(binaries_directory, 'Release')

    ctx.copy_binary_artifacts_from_build(binaries_directory, out_path)
