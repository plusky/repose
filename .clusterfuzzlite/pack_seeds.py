#!/usr/bin/env python3
"""Build one libFuzzer seed corpus archive.

Usage: pack_seeds.py <out.zip> <path>...

Paths are files or directories (walked recursively). Written in Python
because the oss-fuzz base images ship no `zip` binary, only CPython.
"""

import hashlib
import os
import sys
import zipfile

# Fixed so a rebuild of unchanged seeds produces a byte-identical archive.
EPOCH = (1980, 1, 1, 0, 0, 0)


def walk(paths):
    for path in paths:
        if os.path.isdir(path):
            for root, _, names in os.walk(path):
                for name in sorted(names):
                    yield os.path.join(root, name)
        elif os.path.isfile(path):
            yield path


def main(argv):
    out, paths = argv[1], argv[2:]
    # Content-addressed entries deduplicate the .prod files shared between
    # refhosts and sidestep the basename collisions a flat archive would hit.
    seeds = {}
    for path in walk(paths):
        with open(path, "rb") as handle:
            data = handle.read()
        seeds[hashlib.sha256(data).hexdigest()] = data
    if not seeds:
        sys.exit(f"pack_seeds: no seed inputs under {' '.join(paths)}")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(seeds.items()):
            # A ZipInfo carries its own compress_type, which would otherwise
            # default to stored and quietly ignore the archive's setting.
            info = zipfile.ZipInfo(name, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    print(f"pack_seeds: {len(seeds)} seeds -> {out}")


if __name__ == "__main__":
    main(sys.argv)
