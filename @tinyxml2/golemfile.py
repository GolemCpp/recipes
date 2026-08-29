import os
import sys
import shutil
import subprocess


def configure(project):
    def artifacts_generator(decorated_target, config, context):
        artifacts = []
        for suffix in context.artifact_suffix(config):
            artifact = context.artifact_prefix(config) + decorated_target + suffix
            artifacts.append(artifact)
            if suffix == ".so":
                artifacts.append("{}.{}".format(artifact, context.version.major))
                artifacts.append(
                    "{}.{}.{}.{}".format(
                        artifact,
                        context.version.major,
                        context.version.minor,
                        context.version.patch,
                    )
                )
            elif suffix == ".dylib":
                basename_prefix = context.artifact_prefix(config) + decorated_target
                artifacts.append(
                    "{}.{}.dylib".format(basename_prefix, context.version.major)
                )
                artifacts.append(
                    "{}.{}.{}.{}.dylib".format(
                        basename_prefix,
                        context.version.major,
                        context.version.minor,
                        context.version.patch,
                    )
                )
        return artifacts

    target = project.library(
        name="tinyxml2", scripts=[script], artifacts_generators=[artifacts_generator]
    )

    target.when(variant="debug", targets=["tinyxml2d"])
    target.when(variant="release", targets=["tinyxml2"])

    target = project.export(
        name="tinyxml2", includes=["include"], licenses=["LICENSE.txt"]
    )


def script(ctx):

    src_dir = ctx.get_project_dir()

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    variant = None
    if ctx.is_debug():
        variant = "Debug"
    else:
        variant = "Release"

    opt_variant = "-DCMAKE_BUILD_TYPE=" + variant

    opt_target_shared = "-DBUILD_SHARED_LIBS:BOOL="
    if ctx.is_static():
        opt_target_shared += "OFF"
    else:
        opt_target_shared += "ON"

    opt_target_static = "-DBUILD_STATIC_LIBS:BOOL="
    if ctx.is_static():
        opt_target_static += "ON"
    else:
        opt_target_static += "OFF"

    opt_target = [opt_target_shared, opt_target_static]

    opt_arch = ["-A", ctx.vs_platform()] if ctx.is_windows() else []

    ret = subprocess.call(
        ["cmake", src_dir]
        + opt_arch
        + [opt_variant, "-DBUILD_TESTS:BOOL=OFF"]
        + opt_target,
        cwd=target_dir,
    )
    if ret:
        print("ERROR: cmake")
        return

    ret = subprocess.call(
        ["cmake", "--build", ".", "--config", variant], cwd=target_dir
    )
    if ret:
        print("ERROR: cmake --build")
        return

    out_path = ctx.make_out_path()
    if ctx.is_windows():
        ctx.copy_binary_artifacts_from_build(
            os.path.join(target_dir, variant), out_path
        )
    else:
        ctx.copy_binary_artifacts_from_build(os.path.join(target_dir), out_path)

    include_dir = os.path.join(src_dir, "include")
    if not os.path.exists(include_dir):
        os.makedirs(include_dir)
    shutil.copy2(os.path.join(src_dir, "tinyxml2.h"), include_dir)
