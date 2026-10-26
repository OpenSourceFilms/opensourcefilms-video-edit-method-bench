#!/usr/bin/env python3
"""Stage the four historical comparison inputs without overwriting user files.

The inputs are personal shot assets, not included in this public repository.
Perform a complete existence/conflict preflight before creating directories.
Both copy and link modes publish only to previously absent destination names.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile

FILES = [
    "orbit_and_turn_4K8Bit_01.mov",
    "Orbit_and_turn_Firstframe_Flames_1088p_01.png",
    "Orbit_and_turn_Middleframe_Flames_1088p_02.png",
    "Orbit_and_turn_Lastframe_Flames_1088p_02.png",
]


def _exclusive_copy(source: Path, target: Path) -> None:
    """Publish a complete copied file without exposing partial target bytes.

    The source is streamed into a private temporary file alongside the final
    destination and fsynced before the final name exists. Same-filesystem
    hard-link creation claims the destination atomically and refuses existing
    files or dangling symlinks without overwriting them. Only our temporary
    file is removed on failure, including a competing destination race.
    """
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".staging", dir=target.parent
    )
    try:
        with os.fdopen(fd, "wb") as writer:
            with source.open("rb") as reader:
                shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        os.link(temp_name, target, follow_symlinks=False)
    finally:
        # No target cleanup: a contender may have published it meanwhile.
        # Successful publication leaves a complete hard-linked target inode.
        os.unlink(temp_name)



def stage_inputs(comfy_root: Path, shot_dir: Path, *, copy: bool = False) -> list[Path]:
    source_dir = Path(shot_dir)
    destination_dir = Path(comfy_root) / "input"
    if destination_dir.is_symlink():
        raise ValueError("Refusing a symlinked ComfyUI input directory")
    if destination_dir.exists() and not destination_dir.is_dir():
        raise ValueError("ComfyUI input destination is not a directory")

    # A missing late reference frame must not leave partial staged output.
    # Source symlinks to regular files are allowed: operators may mount
    # their own shot media from other storage.
    plan = []
    for name in FILES:
        source = source_dir / name
        target = destination_dir / name
        if not source.is_file():
            raise FileNotFoundError("Missing or non-regular source: " + str(source))
        if target.exists() or target.is_symlink():
            if not target.is_file() or target.resolve() != source.resolve():
                raise FileExistsError(
                    str(target) + " exists and does not point to " + str(source)
                )
            plan.append(("already", source, target))
        else:
            plan.append(("create", source, target))

    destination_dir.mkdir(parents=True, exist_ok=True)
    staged = []
    for action, source, target in plan:
        if action == "already":
            print("OK", target)
        elif copy:
            _exclusive_copy(source, target)
            print("COPIED", target, "->", source)
        else:
            # symlink_to() also refuses existing files and dangling symlinks.
            target.symlink_to(source.resolve())
            print("LINKED", target, "->", source)
        staged.append(target)
    return staged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy-root", required=True)
    parser.add_argument(
        "--shot-dir", required=True,
        help="directory holding your own source plate and reference frames",
    )
    parser.add_argument("--copy", action="store_true", help="copy instead of symlink")
    args = parser.parse_args(argv)
    stage_inputs(Path(args.comfy_root), Path(args.shot_dir), copy=args.copy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
