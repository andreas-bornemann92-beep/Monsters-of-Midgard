#!/usr/bin/env python3
"""Import only KORTEX engine and rule profiles from the verified handoff ZIP."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import zipfile

ALLOWED = ("kortex/engine/", "kortex/05_KORTEX/")
REQUIRED = {
    "kortex/engine/kortex_battle/master.py",
    "kortex/engine/smoke_test_master.py",
    "kortex/engine/test_stat_reference.py",
    "kortex/05_KORTEX/TYPENPROFIL_V0_6.json",
    "kortex/05_KORTEX/GRAPH.json",
}

def import_archive(archive: Path, checkout: Path, dry_run=False):
    if not (checkout / ".git").exists():
        raise ValueError("Checkout must contain .git")
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f"Damaged archive member: {bad}")
        files = {}
        for item in z.infolist():
            name = item.filename
            if item.is_dir() or "__pycache__/" in name or name.endswith(".pyc"):
                continue
            if not name.startswith(ALLOWED):
                continue
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe path: {name}")
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"Symlink forbidden: {name}")
            if name in files:
                raise ValueError(f"Duplicate entry: {name}")
            files[name] = z.read(item)
        if not REQUIRED.issubset(files):
            raise ValueError(f"Missing required files: {sorted(REQUIRED-set(files))}")
        hashes = {name: hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
        if not dry_run:
            for name,data in files.items():
                dest = checkout.joinpath(*PurePosixPath(name).parts)
                current = dest
                while current != checkout:
                    if current.is_symlink():
                        raise ValueError(f"Unsafe destination symlink: {current}")
                    current = current.parent
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(data)
            for name,digest in hashes.items():
                if hashlib.sha256(checkout.joinpath(*PurePosixPath(name).parts).read_bytes()).hexdigest()!=digest:
                    raise ValueError(f"Failed postwrite verification: {name}")
    return {"count":len(files),"sha256":hashes,"dry_run":dry_run}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("archive",type=Path)
    p.add_argument("--checkout",type=Path,default=Path("."))
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    result=import_archive(args.archive,args.checkout.resolve(),args.dry_run)
    print(json.dumps({"files":result["count"],"verified":True,"dry_run":args.dry_run},indent=2))
