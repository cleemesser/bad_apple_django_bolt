# /// script
# requires-python = ">=3.13"
# ///
"""Concatenate cascii per-frame .txt files into a single blob and augment details.toml.

Reads cascii output from a directory (default ./bad_apple) containing frame_NNNN.txt
files and details.toml, writes a concatenated bad_apple_all.txt, and appends
frame_size to details.toml if it's not already there.
"""
import argparse
import os
import pathlib
import shutil
import sys
import tomllib


def frame_index(fpath: pathlib.Path) -> int:
    return int(fpath.stem.split("_")[1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        type=pathlib.Path,
        default=pathlib.Path("./bad_apple"),
        help="Directory with cascii frame_*.txt files and details.toml",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Concatenated output path (default: <dir>/bad_apple_all.txt)",
    )
    args = parser.parse_args()

    data_dir: pathlib.Path = args.dir
    output: pathlib.Path = args.output or (data_dir / "bad_apple_all.txt")
    details_path = data_dir / "details.toml"

    ### start doing things

    # now copy audio.mp3 to ./static/audio.mp3
    pathlib.Path('./static').mkdir(exist_ok=True)
    shutil.copyfile("bad_apple/audio.mp3", "./static/audio.mp3")


    with open(details_path, "rb") as fp:
        details = tomllib.load(fp)

    frame_paths = sorted(data_dir.glob("frame_*.txt"), key=frame_index)
    if len(frame_paths) != details["frames"]:
        print(
            f"ERROR: details.toml says frames={details['frames']} "
            f"but found {len(frame_paths)} frame_*.txt files in {data_dir}",
            file=sys.stderr,
        )
        return 1

    frame_size = os.path.getsize(frame_paths[0])
    for p in frame_paths:
        sz = os.path.getsize(p)
        if sz != frame_size:
            print(
                f"ERROR: {p.name} size {sz} != first frame size {frame_size}",
                file=sys.stderr,
            )
            return 1

    with open(output, "wb") as out_fp:
        for p in frame_paths:
            with open(p, "rb") as in_fp:
                out_fp.write(in_fp.read())

    total = os.path.getsize(output)
    expected = details["frames"] * frame_size
    if total != expected:
        print(
            f"ERROR: {output} size {total} != frames*frame_size {expected}",
            file=sys.stderr,
        )
        return 1

    existing = details.get("frame_size")
    if existing is None:
        with open(details_path, "rb") as fp:
            current = fp.read()
        sep = b"" if current.endswith(b"\n") else b"\n"
        with open(details_path, "ab") as fp:
            fp.write(sep + f"frame_size = {frame_size}\n".encode("ascii"))
    elif existing != frame_size:
        print(
            f"ERROR: details.toml has frame_size={existing} but measured {frame_size}",
            file=sys.stderr,
        )
        return 1

    print(
        f"wrote {output} ({total} bytes = {details['frames']} frames x {frame_size} bytes)"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
