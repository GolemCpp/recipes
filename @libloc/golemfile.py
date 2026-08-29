import os
import shutil
import subprocess


def configure(project):

    project.dependency(
        name='openssl',
        location='@openssl',
        version='*',
        variant="release",
        shallow=True,
    )

    def artifacts_generator(decorated_target, config, context):
        artifacts = []
        for suffix in context.artifact_suffix(config):
            artifact = context.artifact_prefix(config) + decorated_target + suffix
            artifacts.append(artifact)
            if suffix == '.so':
                artifacts.append('{}.{}'.format(artifact, context.version.major))
                artifacts.append(
                    '{}.{}.{}.{}'.format(
                        artifact,
                        context.version.major,
                        context.version.minor,
                        context.version.patch,
                    )
                )
            elif suffix == '.dylib':
                basename_prefix = context.artifact_prefix(config) + decorated_target
                artifacts.append(
                    '{}.{}.dylib'.format(basename_prefix, context.version.major)
                )
                artifacts.append(
                    '{}.{}.{}.{}.dylib'.format(
                        basename_prefix,
                        context.version.major,
                        context.version.minor,
                        context.version.patch,
                    )
                )
        return artifacts

    task = project.library(
        name='libloc',
        targets=['loc'],
        deps=['openssl'],
        scripts=[script],
        artifacts_generators=[artifacts_generator],
    )

    task.when(
        osystem='linux',
        packages=[],
        packages_dev=['autoconf', 'intltool', 'asciidoc', 'pkg-config'],
    )

    project.export(
        name='libloc', includes=['include'], licenses=['COPYING'], deps=['openssl']
    )


def build_gcc(ctx):

    repo_dir = ctx.get_project_dir()

    ret = subprocess.call(['intltoolize', '--force', '--automake'], cwd=repo_dir)
    if ret:
        raise RuntimeError("ERROR: intltoolize")

    ret = subprocess.call(['autoreconf', '--install', '--symlink'], cwd=repo_dir)
    if ret:
        raise RuntimeError("ERROR: autoreconf")

    configure_options = ['--prefix=/usr/local', '--libdir=/usr/local/lib']
    configure_cflags = []
    configure_ldflags = []

    if ctx.is_debug():
        configure_cflags += ['-g', '-O0']

    if ctx.is_static():
        configure_options += ['--enable-static=yes', '--enable-shared=no']
    else:
        configure_options += ['--enable-static=no', '--enable-shared=yes']

    configure_cflags += ['-I{}'.format(ctx.find_dependency_includes('openssl')[0])]
    configure_ldflags += ['-L{}'.format(ctx.find_dependency_libraries('openssl')[0])]

    my_env = dict()
    my_env['PATH'] = os.environ['PATH']
    my_env['CFLAGS'] = ' '.join(configure_cflags)
    my_env['LDFLAGS'] = ' '.join(configure_ldflags)
    configure_command = ['./configure'] + configure_options

    subprocess.call(['make', 'clean'], cwd=repo_dir, env=my_env)

    print("CFLAGS={}".format(' '.join(configure_cflags)))
    print("LDFLAGS={}".format(' '.join(configure_ldflags)))
    print("{}".format(' '.join(configure_command)))

    ret = subprocess.call(configure_command, cwd=repo_dir, env=my_env)
    if ret:
        raise RuntimeError("ERROR: configure")

    ret = subprocess.call(['make'], cwd=repo_dir, env=my_env)
    if ret:
        raise RuntimeError("ERROR: make")

    artifact_dir = os.path.join(repo_dir, 'src', '.libs')

    out_path = ctx.make_out_path()
    ctx.copy_binary_artifacts_from_build(artifact_dir, out_path)


def script(ctx):

    if ctx.compiler_name() == 'msvc':
        raise RuntimeError("Cannot compile libloc with msvc")
    else:
        build_gcc(ctx)

    repo_dir = ctx.get_project_dir()

    include_dir = os.path.join(repo_dir, 'include')
    if os.path.exists(include_dir):
        shutil.rmtree(include_dir)
    os.makedirs(include_dir)

    shutil.copytree(
        os.path.join(repo_dir, 'src', 'libloc'),
        os.path.join(include_dir, 'libloc'),
        dirs_exist_ok=True,
    )
