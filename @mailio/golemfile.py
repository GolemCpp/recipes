def configure(project):

    project.dependency(
        name='boost',
        targets=["boost_system", "boost_date_time", "boost_regex"],
        location='@boost',
        version='*',
        variant='release',
        shallow=True,
        link='static',
    )

    project.dependency(
        name='openssl',
        location='@openssl',
        version='*',
        variant="release",
        shallow=True,
    )

    project.library(name='mailio', deps=['boost', 'openssl'], scripts=[script])

    project.export(
        name='mailio',
        includes=['include'],
        licenses=['LICENSE'],
        deps=['boost', 'openssl'],
    )


import os
import sys
import shutil
import subprocess


def script(ctx):

    mailio_dir = ctx.get_project_dir()

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    variant = None
    if ctx.is_debug():
        variant = 'Debug'
    else:
        variant = 'Release'

    opt_variant = '-DCMAKE_BUILD_TYPE=' + variant

    opt_target = '-DMAILIO_BUILD_SHARED_LIBRARY='
    if ctx.is_static():
        opt_target += 'OFF'
    else:
        opt_target += 'ON'

    opt_arch = ['-A', ctx.vs_platform()] if ctx.is_windows() else []

    opt_deps = []

    crypto_libs = ctx.find_dependency_libraries_files(
        dep_name='openssl', target_name='crypto'
    )
    ssl_libs = ctx.find_dependency_libraries_files(
        dep_name='openssl', target_name='ssl'
    )
    ssl_libraries = ssl_libs[0] + ";" + crypto_libs[0]

    opt_deps += [
        '-DBOOST_LIBRARYDIR=' + ctx.find_dependency_libraries('boost')[0],
        '-DBOOST_INCLUDEDIR=' + ctx.find_dependency_includes('boost')[0],
        '-DBoost_NO_SYSTEM_PATHS=ON',
        '-DOPENSSL_LIBRARIES=' + ssl_libraries,
        '-DOPENSSL_CRYPTO_LIBRARY=' + crypto_libs[0],
        '-DOPENSSL_SSL_LIBRARY=' + ssl_libs[0],
        '-DOPENSSL_INCLUDE_DIR=' + ctx.find_dependency_includes('openssl')[0],
    ]

    command = (
        ['cmake', mailio_dir]
        + opt_arch
        + [
            opt_variant,
            opt_target,
            '-DMAILIO_BUILD_DOCUMENTATION=OFF',
            '-DMAILIO_BUILD_EXAMPLES=OFF',
        ]
        + opt_deps
    )

    print(' '.join(command))

    ret = subprocess.call(command, cwd=target_dir)
    if ret:
        raise RuntimeError("ERROR: cmake")

    ret = subprocess.call(
        ['cmake', '--build', '.', '--target', 'mailio', '--config', variant],
        cwd=target_dir,
    )
    if ret:
        raise RuntimeError("ERROR: cmake --build")

    version_file = ctx.make_project_path(os.path.join('include', 'version.hpp.in'))
    if os.path.exists(version_file):
        os.remove(version_file)

    mailio_include_dir = ctx.make_project_path(os.path.join('include', 'mailio'))

    version_file = os.path.join(target_dir, 'version.hpp')
    if os.path.exists(version_file):
        shutil.copyfile(
            src=version_file, dst=os.path.join(mailio_include_dir, 'version.hpp')
        )

    export_file = os.path.join(target_dir, 'export.hpp')
    if os.path.exists(export_file):
        shutil.copyfile(
            src=export_file, dst=os.path.join(mailio_include_dir, 'export.hpp')
        )

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(target_dir, out_path)
