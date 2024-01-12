#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bucket_path", help="Bucket path for the object")
    parser.add_argument(
        "filesystem_prefix",
        help=(
            "Prefix of the filesystem containing the accession directory."
            " Will be stripped from the destination path"
        ),
    )
    parser.add_argument(
        "acc_dir_relative",
        help="Relative path to the accession directory to upload",
    )
    parser.add_argument(
        "--compression_level",
        type=int,
        default=9,
        help="Compression level for gzip",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the object if it already exists",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if not re.match(r"^\d{4}\/\d{2}\/\d{2}/\w*/?$", args.acc_dir_relative):
        print(
            f"Invalid format for acc_dir_relative: '{args.acc_dir_relative}'",
            file=sys.stderr,
        )
        return 1

    acc_dir_abs = os.path.join(args.filesystem_prefix, args.acc_dir_relative)
    object_path = f"{os.path.join(args.bucket_path, args.acc_dir_relative)}.tar.gz"

    stat_cmd = ("mc", "stat", "--json", object_path)
    if args.debug:
        subprocess.check_call(("echo", *stat_cmd))
    proc = subprocess.run(stat_cmd, capture_output=True)
    stat_json = json.loads(proc.stdout.decode())
    if args.debug:
        print(stat_json)
    existing_md5 = None
    if proc.returncode == 0 and not args.overwrite:
        print(
            f"Object already exists: '{object_path}'. Will compare checksums",
            file=sys.stderr,
        )
        existing_md5 = stat_json["metadata"]["X-Amz-Meta-Content-Md5"]

    file_count = 0
    modalities = set()
    for name in os.listdir(acc_dir_abs):
        full_name = os.path.join(acc_dir_abs, name)
        if not os.path.isfile(full_name):
            print(f"Encountered a directory {full_name}", file=sys.stderr)
            return 1

        modality = name.split(".")[0]
        if not 2 <= len(modality) <= 3:
            print(f"Unexpected modality prefix on file {full_name}", file=sys.stderr)
            return 1

        modalities.add(modality)
        file_count += 1

    if not file_count:
        print(f"No files found in {acc_dir_abs}", file=sys.stderr)
        return 1

    tar_cmd = (
        "tar",
        "-cO",
        f"--use-compress-program=''/usr/bin/gzip -{args.compression_level}''",
        "-C",
        acc_dir_abs,
        ".",
    )
    if args.debug:
        subprocess.check_call(("echo", *tar_cmd))
    tar_data = subprocess.check_output(tar_cmd)
    tar_md5 = hashlib.md5(tar_data).hexdigest()

    if not args.overwrite:
        if existing_md5 == tar_md5:
            return 0
        print(
            f"MD5 {tar_md5} did not match existing {existing_md5} for {acc_dir_abs}",
            file=sys.stderr,
        )
        return 1

    attrs = {
        "Content-MD5": tar_md5,
        "Total-Count": file_count,
        "Modalities": ",".join(sorted(modalities)),
    }

    pipe_cmd = (
        "mc",
        "pipe",
        "--quiet",
        "--attr",
        ";".join([f"{k}={v}" for k, v in attrs.items()]),
        object_path,
    )
    if args.debug:
        subprocess.check_call(("echo", *pipe_cmd))
    subprocess.run(pipe_cmd, input=tar_data, check=True, stdout=subprocess.DEVNULL)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
