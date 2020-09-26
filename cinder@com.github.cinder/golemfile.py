#!/usr/bin/env python

from tempfile import mkstemp
import os
from os import fdopen, remove
from shutil import move
from glob import glob
import distutils
import subprocess
import shutil
import sys


def configure(project):

    target = project.export(name='cinder',
                            targets=['cinder'],
                            includes=['Cinder/include'])

    target.when(osystem='linux',
                defines=[
                    'FT2_BUILD_LIBRARY', 'FT_DEBUG_LEVEL_TRACE', '_GLFW_X11',
                    '_UNIX'
                ])

    target.when(osystem='linux',
                system=[
                    'GLU', 'GL', 'SM', 'ICE', 'X11', 'Xext', 'Xcursor',
                    'Xinerama', 'Xrandr', 'Xi', 'z', 'curl', 'fontconfig',
                    'pulse', 'mpg123', 'sndfile', 'gobject-2.0', 'glib-2.0',
                    'gstreamer-1.0', 'gstbase-1.0', 'gstapp-1.0',
                    'gstvideo-1.0', 'gstgl-1.0', 'boost_system',
                    'boost_filesystem', 'dl'
                ])

    target.when(osystem='linux',
                distribution='debian',
                release='buster',
                packages=[
                    'libcurl4', 'libfontconfig1', 'libpulse0', 'libmpg123-0',
                    'libsndfile1', 'libgstreamer1.0-0',
                    'libgstreamer-plugins-base1.0-0', 'libxrandr2',
                    'libxcursor1', 'libxinerama1', 'libxi6', 'libsm6'
                ],
                packages_dev=[
                    'libcurl4-openssl-dev', 'libfontconfig1-dev',
                    'libpulse-dev', 'libmpg123-dev', 'libsndfile1-dev',
                    'libgstreamer1.0-dev', 'libgstreamer-plugins-base1.0-dev',
                    'libxrandr-dev', 'libxcursor-dev', 'libxinerama-dev',
                    'libxi-dev', 'libsm-dev'
                ])

    target.when(osystem='windows', defines=['CINDER_SHARED'])


def line_in_file(file_path, text):

    linelist = []
    with open(file_path, 'r') as file:
        linelist = file.readlines()

    found = False
    for line in linelist:
        if text in line:
            found = True
            break

    if not found:
        with open(file_path, 'a') as file:
            file.write(text + "\n")


def patch_cmake_for_windows(cinder_dir):
    cmake_path = os.path.join(cinder_dir, 'proj', 'cmake',
                              'platform_msw.cmake')
    line_in_file(
        cmake_path,
        'include( ${CMAKE_CURRENT_LIST_DIR}/platform_msw_patch.cmake )')

    patch_path = os.path.join(cinder_dir, 'proj', 'cmake',
                              'platform_msw_patch.cmake')

    with open(patch_path, 'w+') as file:
        file.writelines([
            'list( APPEND CINDER_SRC_FILES ${CINDER_SRC_DIR}/videoInput/videoInput.cpp )'
            + "\n",
            'list( REMOVE_ITEM CINDER_SRC_FILES ${CINDER_SRC_DIR}/cinder/app/AppScreenSaver.cpp )'
            + "\n",
            'list( REMOVE_ITEM CINDER_SRC_FILES ${CINDER_SRC_DIR}/cinder/app/msw/AppImplMswScreenSaver.cpp )'
            + "\n",
            'list( APPEND CINDER_DEFINES "CINDER_SHARED_BUILD;JSON_DLL_BUILD" )'
            + '\n', 'foreach( ' + "\n", 'flag_var' + "\n",
            'CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELEASE CMAKE_C_FLAGS_MINSIZEREL CMAKE_C_FLAGS_RELWITHDEBINFO '
            + "\n",
            'CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE CMAKE_CXX_FLAGS_MINSIZEREL CMAKE_CXX_FLAGS_RELWITHDEBINFO '
            + "\n", ')' + "\n", 'if( ${flag_var} MATCHES "/MT" )' + "\n",
            'string( REGEX REPLACE "/MT" "/MD" ${flag_var} "${${flag_var}}" )'
            + "\n", 'endif()' + "\n", 'endforeach()' + "\n",
            'include_directories( ${CINDER_SRC_DIR}/../include/msw )' + '\n',
            'set( CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} /LIBPATH:..\\\\..\\\\lib\\\\msw\\\\x64 /DYNAMICBASE ${MSW_PLATFORM_LIBS} /NODEFAULTLIB:LIBCMT /NODEFAULTLIB:LIBCPMT" )'
            + "\n"
        ])


def patch_pull_request_2070(ctx):
    shutil.copy(
        ctx.make_project_path(os.path.join('patch', '_int_glx_type.h')),
        ctx.make_project_path(
            os.path.join('Cinder', 'include', 'glload', '_int_glx_type.h')))
    shutil.copy(
        ctx.make_project_path(os.path.join('patch', '_int_glx_type.hpp')),
        ctx.make_project_path(
            os.path.join('Cinder', 'include', 'glload', '_int_glx_type.hpp')))


def replace_in_file(file_path, pattern, subst):

    # Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))

        # Remove original file
    remove(file_path)

    # Move new file
    move(abs_path, file_path)


def patch_src_for_windows(cinder_dir):
    file_include_params_params = os.path.join(cinder_dir, 'include', 'cinder',
                                              'params', 'Params.h')
    replace_in_file(file_include_params_params, 'class CI_API Options :',
                    'class Options :')
    replace_in_file(file_include_params_params, 'Options&', 'inline Options&')


def script(ctx):

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    cinder_dir = ctx.make_project_path('Cinder')

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

    opt_arch = ['-A']
    if ctx.is_x64():
        opt_arch.append('x64')
    else:
        opt_arch.append('x86')

    opt_windows = []
    if ctx.is_windows():
        opt_windows += opt_arch
        patch_src_for_windows(cinder_dir)
        patch_cmake_for_windows(cinder_dir)

    patch_pull_request_2070(ctx)

    opt_linux = []
    if ctx.is_linux():
        opt_linux.append('-DCINDER_BOOST_USE_SYSTEM=1')

    cmd = ['cmake', cinder_dir] + [opt_variant, opt_target
                                   ] + opt_linux + opt_windows
    print cmd
    ret = subprocess.call(cmd, cwd=target_dir)
    if ret:
        print "ERROR: cmake"
        return

    cmd = ['cmake', '--build', '.', '--config', variant]
    print cmd
    ret = subprocess.call(cmd, cwd=target_dir)
    if ret:
        print "ERROR: cmake --build"
        return

    out_path = ctx.make_out_path()

    if ctx.is_linux():
        ctx.copy_binary_artifacts(
            os.path.join(cinder_dir, 'lib', 'linux', 'x86_64', 'ogl', variant),
            out_path)

    elif ctx.is_windows():
        path = os.path.join(cinder_dir, 'lib', 'msw',
                            'x64' if ctx.is_x64() else 'x86', variant)
        full_paths = glob(path + '/*')
        for path in full_paths:
            if os.path.basename(os.path.normpath(path)).startswith(
                    'v') and os.path.isdir(path):
                ctx.copy_binary_artifacts(path, out_path)

        path = os.path.join(target_dir, variant)
        ctx.copy_binary_artifacts(path, out_path)
