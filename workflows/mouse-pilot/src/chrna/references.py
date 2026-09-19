"""Fetch explicitly pinned public references with streaming integrity checks."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def file_hashes(path: Path) -> tuple[str, str]:
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def fetch_reference(spec: dict, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt = Path(str(target) + ".provenance.json")
    with Path(str(target) + ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if target.exists():
            md5, sha = file_hashes(target)
            if md5 != spec["md5"]:
                raise ValueError(f"Cached reference checksum mismatch: {target}")
        else:
            if not spec["url"].startswith("https://"):
                raise ValueError("Reference transfer requires HTTPS")
            partial = Path(str(target) + ".partial")
            size = 0
            with urllib.request.urlopen(spec["url"], timeout=120) as response, partial.open("wb") as out:
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > spec["max_bytes"]:
                        raise ValueError("Reference exceeds declared transfer limit")
                    out.write(chunk)
            md5, sha = file_hashes(partial)
            if md5 != spec["md5"]:
                raise ValueError(f"Downloaded reference checksum mismatch: {target}")
            os.replace(partial, target)
        if receipt.exists():
            record = json.loads(receipt.read_text())
            if record["sha256"] != sha or record["url"] != spec["url"] or record["md5"] != md5:
                raise ValueError("Reference receipt mismatch")
            return record
        record = {**spec, "sha256": sha, "bytes": target.stat().st_size,
                  "verified_utc": datetime.now(timezone.utc).isoformat()}
        with receipt.open("x") as handle:
            json.dump(record, handle, indent=2)
            handle.write("\n")
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    spec = manifest["files"][args.name]
    print(json.dumps(fetch_reference(spec, args.directory / args.name), indent=2))


if __name__ == "__main__":
    main()
