#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


def configure(project):
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
                                                context.version.minor))
                artifacts.append('{}.{}.{}.{}'.format(artifact,
                                                      context.version.major,
                                                      context.version.minor,
                                                      context.version.patch))
            elif suffix == '.dylib':
                basename_prefix = context.artifact_prefix(
                    config) + decorated_target
                artifacts.append('{}.{}.dylib'.format(basename_prefix,
                                                      context.version.minor))
                artifacts.append('{}.{}.{}.{}.dylib'.format(
                    basename_prefix, context.version.major,
                    context.version.minor, context.version.patch))
        return artifacts

    project.dependency(name='json',
                       repository='https://github.com/nlohmann/json.git',
                       version='~3.7.0',
                       variant="release",
                       shallow=True)

    project.library(name='json-schema-validator',
                    targets=['nlohmann_json_schema_validator'],
                    scripts=[script],
                    deps=['json'],
                    target_decorators=[target_decorator],
                    artifacts_generators=[artifacts_generator])

    project.export(name='json-schema-validator',
                   includes=['include'],
                   deps=['json'],
                   licenses=['LICENSE'])


def script(ctx):

    ctx.build_dependency('json')

    json_includes = ctx.find_dependency_includes('json')
    if not json_includes:
        raise Exception("Error: Can't find json include directory")

    json_include = json_includes[0]

    source_path = ctx.get_project_dir()

    cmake_options = ['-Dnlohmann_json_DIR=' + json_include]

    if ctx.is_windows():
        cmake_options.append('-DCMAKE_CXX_FLAGS=/std:c++17')

    ctx.cmake_build(source_path=source_path,
                    targets=['nlohmann_json_schema_validator'],
                    options=cmake_options)

    ctx.export_binaries(recursively=True)

    ctx.export_file_to_headers(
        file_path=os.path.join(source_path, 'src', 'nlohmann',
                               'json-schema.hpp'),
        include_path=os.path.join('include', 'json-schema-validator'))
