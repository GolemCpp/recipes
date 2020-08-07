#!/usr/bin/env python3

import os
import shutil
import subprocess


def configure(project):
    project.library(name='zlib', targets=['z'], scripts=[script])
    project.export(name='zlib', includes=['include'], licenses=['README'])


def script(ctx):

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
    ctx.copy_binary_artifacts(repo_dir, out_path)

    include_dir = os.path.join(repo_dir, 'include')
    if os.path.exists(include_dir):
        shutil.rmtree(include_dir)
    os.makedirs(include_dir)

    shutil.copy(os.path.join(repo_dir, 'zlib.h'), include_dir)
    shutil.copy(os.path.join(repo_dir, 'zconf.h'), include_dir)
