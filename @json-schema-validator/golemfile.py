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
                       location='@json@nlohmann',
                       version='*',
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

    json = ctx.find_dependency('json')
    if not json:
        raise Exception("Error: Can't find json dependency")

    source_path = ctx.get_project_dir()

    cmake_env = {
        'NLOHMANN_JSON_VERSION': json.resolved.reference
    }
    
    cmake_options = []

    if ctx.is_windows():
        cmake_options.append('-DCMAKE_CXX_FLAGS=/std:c++17')

    ctx.cmake_build(source_path=source_path,
                    targets=['nlohmann_json_schema_validator'],
                    options=cmake_options,
                    env=cmake_env)

    ctx.export_binaries(recursively=True)

    ctx.export_file_to_headers(
        file_path=os.path.join(source_path, 'src', 'nlohmann',
                               'json-schema.hpp'),
        include_path=os.path.join('include', 'json-schema-validator'))
