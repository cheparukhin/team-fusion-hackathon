"""Install the pinned public SRA Toolkit inside the project, without configuring accounts."""
import argparse
import json
import platform
import tarfile
from pathlib import Path

from chrna.intake import sha256
from chrna.references import fetch_reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("workflow/tools/sratoolkit-3.2.1.json"))
    parser.add_argument("--directory", type=Path, default=Path(".tools"))
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        parser.error("The pinned toolkit distribution requires Linux x86_64")
    spec = json.loads(args.manifest.read_text())
    package = args.directory / "downloads" / spec["url"].rsplit("/", 1)[1]
    receipt = fetch_reference({key: spec[key] for key in ("url", "md5", "max_bytes")}, package)
    if receipt["sha256"] != spec["sha256"]:
        raise ValueError("Toolkit archive differs from the pinned SHA-256")
    target = args.directory / spec["directory"]
    if not target.exists():
        with tarfile.open(package) as archive:
            archive.extractall(args.directory, filter="data")
    for name, expected in spec["executable_sha256"].items():
        if sha256(target / "bin" / name) != expected:
            raise ValueError(f"Installed executable differs from pinned build: {name}")
    print(f"Verified SRA Toolkit {spec['version']}: {target}")


if __name__ == "__main__":
    main()
