#!/usr/bin/env python3

import os
import shutil
import subprocess


def configure(project):

    task = project.library(name='llhttp',
                           includes=['include'],
                           source=['src'],
                           defines=['LLHTTP_STRICT_MODE=1'])

    task.when(variant='debug', cppflags=['-O0', '-g3'])
    task.when(variant='release', cppflags=['-O3', '-g0'])

    project.export(name='llhttp',
                   includes=['include'],
                   licenses=['LICENSE-MIT'],
                   defines=['LLHTTP_STRICT_MODE=1'])


"""
def configure(project):

    task = project.library(name='llhttp', scripts=[script])

    task.when(osystem='linux',
              distribution='debian',
              release='buster-backports',
              packages=[],
              packages_dev=['npm', 'node-typescript', 'node-typescript-types'])

    project.export(name='llhttp',
                   includes=['include'],
                   licenses=['LICENSE-MIT'])
"""


def fix_makefile(makefile_path, is_debug):

    fixed_makefile_path = makefile_path + '.fixed'

    with open(makefile_path, 'rt') as fin:
        with open(fixed_makefile_path, 'wt') as fout:
            for line in fin:
                if is_debug:
                    line = line.replace('-Os', '-O0')
                else:
                    line = line.replace('-Os', '-O3').replace('-g3', '')
                fout.write(line)

    shutil.copyfile(src=fixed_makefile_path, dst=makefile_path)


def build_clang(ctx):

    repo_dir = ctx.get_project_dir()

    makefile_path = os.path.join(repo_dir, "Makefile")

    if not os.path.exists(makefile_path):
        raise RuntimeError("Cannot find Makefile at {}".format(makefile_path))

    fix_makefile(makefile_path=makefile_path, is_debug=ctx.is_debug())

    subprocess.call(['npm', 'install'], cwd=repo_dir)

    target = 'build/libllhttp.a'

    if ctx.is_shared():
        target = 'build/libllhttp.so'

    ret = subprocess.call(['make', target], cwd=repo_dir)

    if ret:
        raise RuntimeError("ERROR: make")

    artifact_dir = os.path.join(repo_dir, 'build')

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(artifact_dir, out_path)


def script(ctx):

    if ctx.compiler_name() == 'msvc':
        raise RuntimeError("Cannot compile llhttp with msvc")
    else:
        build_clang(ctx)

    repo_dir = ctx.get_project_dir()

    include_dir = os.path.join(repo_dir, 'include', 'llhttp')
    if os.path.exists(include_dir):
        shutil.rmtree(include_dir)
    os.makedirs(include_dir)

    llhttp_header = os.path.join(repo_dir, 'build', 'llhttp.h')

    shutil.copyfile(src=llhttp_header, dst=include_dir)