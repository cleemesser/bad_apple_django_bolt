# /// script
# requires-python = ">=3.13"
# ///
"""Run cascii against a source video to produce the ASCII frame directory.

Downloads a prebuilt cascii binary from the cascii/cascii GitHub releases into
a user cache if cascii isn't already on PATH. Always passes --audio --default;
tune quality with --fps and --columns. Output is cascii's default layout:
./<input-stem>/ (e.g., ./bad_apple/ for ./bad_apple.mp4).
"""
import argparse
import os
import pathlib
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request


CACHE_DIR = pathlib.Path.home() / ".cache" / "run-cascii"
CACHE_BIN = CACHE_DIR / "cascii"
RELEASE_URL = "https://github.com/cascii/cascii/releases/latest/download/{asset}"


def asset_name_for_platform() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin":
        os_part = "macos"
    elif system == "Linux":
        os_part = "linux"
    else:
        raise RuntimeError(
            f"No prebuilt cascii binary for {system}. "
            "Install manually via `cargo install --git https://github.com/cascii/cascii`."
        )
    if machine in ("arm64", "aarch64"):
        arch_part = "arm64"
    elif machine in ("x86_64", "amd64"):
        arch_part = "x64"
    else:
        raise RuntimeError(
            f"No prebuilt cascii binary for arch {machine}. "
            "Install manually via `cargo install --git https://github.com/cascii/cascii`."
        )
    return f"cascii-{os_part}-{arch_part}.tar.gz"


def download_cascii() -> pathlib.Path:
    """Download the latest-release tarball, extract the cascii binary into CACHE_BIN."""
    asset = asset_name_for_platform()
    url = RELEASE_URL.format(asset=asset)
    print(f"downloading {url}")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tarball = pathlib.Path(td) / asset
        with urllib.request.urlopen(url) as resp, open(tarball, "wb") as fp:
            shutil.copyfileobj(resp, fp)
        with tarfile.open(tarball, "r:gz") as tf:
            member = next(
                (m for m in tf.getmembers() if m.isfile() and pathlib.Path(m.name).name == "cascii"),
                None,
            )
            if member is None:
                raise RuntimeError(f"No 'cascii' file found inside {asset}")
            extracted = pathlib.Path(td) / "extracted"
            tf.extract(member, path=extracted, filter="data")
            shutil.move(str(extracted / member.name), CACHE_BIN)
    CACHE_BIN.chmod(CACHE_BIN.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"cached at {CACHE_BIN}")
    return CACHE_BIN


def find_or_install_cascii() -> str:
    if path := shutil.which("cascii"):
        return path
    if CACHE_BIN.is_file() and os.access(CACHE_BIN, os.X_OK):
        return str(CACHE_BIN)
    return str(download_cascii())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path("bad_apple.mp4"),
        help="Input video file (default: bad_apple.mp4)",
    )
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    parser.add_argument(
        "--columns", type=int, default=100, help="ASCII grid width (default: 100)"
    )
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="Ensure cascii is installed (download if missing) and exit without running it.",
    )
    args = parser.parse_args()

    try:
        cascii_path = find_or_install_cascii()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.install_only:
        print(f"cascii available at {cascii_path}")
        return 0

    if not args.input.is_file():
        print(f"ERROR: input video not found: {args.input}", file=sys.stderr)
        return 1

    cmd = [
        cascii_path,
        str(args.input),
        "--fps", str(args.fps),
        "--columns", str(args.columns),
        "--audio",
        "--default",
    ]
    print("+", " ".join(cmd))
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
