#!/usr/bin/env python3

import os
import shutil
import subprocess


def configure(project):
    def target_decorator(target_name, config, context):
        if context.compiler_name() == 'msvc':
            result = target_name
            result += 'libstat' if context.is_static() else 'libwapi'
            return result
        return target_name

    def artifacts_generator(decorated_target, config, context):
        artifacts = []
        for suffix in context.artifact_suffix(config):
            artifact = context.artifact_prefix(
                config) + decorated_target + suffix
            artifacts.append(artifact)
            if suffix == '.so':
                artifacts.append('{}.{}'.format(artifact,
                                                context.version.major))
                artifacts.append('{}.{}.{}.{}'.format(artifact,
                                                      context.version.major,
                                                      context.version.minor,
                                                      context.version.patch))
            elif suffix == '.dylib':
                basename_prefix = context.artifact_prefix(
                    config) + decorated_target
                artifacts.append('{}.{}.dylib'.format(basename_prefix,
                                                      context.version.major))
                artifacts.append('{}.{}.{}.{}.dylib'.format(
                    basename_prefix, context.version.major,
                    context.version.minor, context.version.patch))
        return artifacts

    project.library(name='zlib',
                    targets=['z'],
                    scripts=[script],
                    target_decorators=[target_decorator],
                    artifacts_generators=[artifacts_generator])

    target = project.export(name='zlib',
                            includes=['include'],
                            licenses=['README'])

    target.when(osystem=['windows'], link=['shared'], defines=['ZLIB_WINAPI'])


def build_msvc(ctx):

    repo_dir = ctx.get_project_dir()

    build_dir = ctx.context.out_dir
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    project_path = os.path.join(repo_dir, 'contrib', 'vstudio', 'vc14')
    build_path = project_path

    if ctx.is_static():
        project_path = os.path.join(project_path, 'zlibstat.vcxproj')
        build_path = os.path.join(
            build_path, ctx.get_arch(),
            'ZlibStat' + ('Release' if ctx.is_release() else 'Debug'))
    else:
        project_path = os.path.join(project_path, 'zlibvc.vcxproj')
        build_path = os.path.join(
            build_path, ctx.get_arch(),
            'ZlibDll' + ('Release' if ctx.is_release() else 'Debug'))

    ctx.run_msbuild_command(project_path=project_path)

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(build_path, out_path)


def build_gcc(ctx):

    repo_dir = ctx.get_project_dir()

    build_dir = ctx.context.out_dir
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    ret = subprocess.call(['./configure'], cwd=repo_dir)
    if ret:
        raise RuntimeError("ERROR: configure")

    ret = subprocess.call(['make'], cwd=repo_dir)
    if ret:
        raise RuntimeError("ERROR: make")

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(repo_dir, out_path)


def script(ctx):

    if ctx.compiler_name() == 'msvc':
        build_msvc(ctx)
    else:
        build_gcc(ctx)

    repo_dir = ctx.get_project_dir()

    include_dir = os.path.join(repo_dir, 'include')
    if os.path.exists(include_dir):
        shutil.rmtree(include_dir)
    os.makedirs(include_dir)

    shutil.copy(os.path.join(repo_dir, 'zlib.h'), include_dir)
    shutil.copy(os.path.join(repo_dir, 'zconf.h'), include_dir)