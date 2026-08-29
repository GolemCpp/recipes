import glob
import subprocess
import shutil
import sys
import os


def configure(project):

    target = project.export(name="assimp", includes=["include"])

    target.when(
        variant="release",
        osystem="linux",
        targets=["assimp"],
        static_targets=["IrrXML"],
    )
    target.when(
        variant="debug",
        osystem="linux",
        targets=["assimpd"],
        static_targets=["IrrXMLd"],
    )

    target.when(
        variant="release",
        osystem="windows",
        targets=["assimp-vc140-mt"],
        static_targets=["IrrXML", "zlib"],
    )
    target.when(
        variant="debug",
        osystem="windows",
        targets=["assimp-vc140-mtd"],
        static_targets=["IrrXMLd", "zlibd"],
    )


def script(ctx):

    target_dir = ctx.context.out_dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    assimp_dir = ctx.make_project_path("assimp")

    variant = None
    if ctx.is_debug():
        variant = "Debug"
    else:
        variant = "Release"

    opt_variant = "-DCMAKE_BUILD_TYPE=" + variant

    opt_target = "-DBUILD_SHARED_LIBS="
    if ctx.is_static():
        opt_target += "0"
    else:
        opt_target += "1"

    opt_windows = []
    if ctx.is_windows():
        opt_windows += ["-A", ctx.vs_platform()]

    opt_linux = []
    opt_linux.append("-DASSIMP_BUILD_TESTS:BOOL=OFF")

    cmd = ["cmake", assimp_dir] + [opt_variant, opt_target] + opt_linux + opt_windows
    print(cmd)
    ret = subprocess.call(cmd, cwd=target_dir)
    if ret:
        print("ERROR: cmake")
        return

    cmd = ["cmake", "--build", ".", "--config", variant]
    print(cmd)
    ret = subprocess.call(cmd, cwd=target_dir)
    if ret:
        print("ERROR: cmake --build")
        return

    out_path = ctx.make_out_path()

    code_path = os.path.join(target_dir, "code")
    irrxml_path = os.path.join(target_dir, "contrib", "irrXML")
    zlib_path = os.path.join(target_dir, "contrib", "zlib")

    if ctx.is_windows():
        code_path = os.path.join(code_path, variant)
        irrxml_path = os.path.join(irrxml_path, variant)
        zlib_path = os.path.join(zlib_path, variant)

    ctx.copy_binary_artifacts_from_build(os.path.join(code_path), out_path)
    ctx.copy_binary_artifacts_from_build(os.path.join(irrxml_path), out_path)

    if ctx.is_windows():
        ctx.copy_binary_artifacts_from_build(os.path.join(zlib_path), out_path)

    shutil.copytree(
        os.path.join(assimp_dir, "include"),
        os.path.join(assimp_dir, "..", "include"),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        os.path.join(target_dir, "include"),
        os.path.join(assimp_dir, "..", "include"),
        dirs_exist_ok=True,
    )
