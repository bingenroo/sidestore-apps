#!/usr/bin/env python3
"""Patch source.json with a freshly released build.

Called by the build workflow in each private source repo, after the .ipa has
been uploaded as a release asset on this (public) repo.

Writes both the AltStore v2 shape (apps[].versions[]) and the legacy v1 fields
(apps[].version / versionDate / downloadURL / size) so old and new SideStore
builds both resolve the same release.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

KEEP_VERSIONS = 10


def version_tuple(v):
    """0.0.12 -> (0, 0, 12). Non-numeric parts sort as -1 so they never win."""
    out = []
    for part in str(v).split("."):
        out.append(int(part) if part.isdigit() else -1)
    return tuple(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="source.json")
    p.add_argument("--template", default="apps.template.json")
    p.add_argument("--bundle-id", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--build", required=True)
    p.add_argument("--download-url", required=True)
    p.add_argument("--size", type=int, required=True)
    p.add_argument("--min-os", default="14.0")
    p.add_argument("--notes", default="")
    p.add_argument("--date", default=date.today().isoformat())
    args = p.parse_args()

    source_path = Path(args.source)
    source = json.loads(source_path.read_text())
    template = json.loads(Path(args.template).read_text())

    app = next(
        (a for a in source["apps"] if a.get("bundleIdentifier") == args.bundle_id),
        None,
    )
    if app is None:
        if args.bundle_id not in template:
            sys.exit(f"no template entry for bundle id {args.bundle_id}")
        app = dict(template[args.bundle_id])
        app["versions"] = []
        source["apps"].append(app)
    app.setdefault("versions", [])

    # A build must never ship under a version already published, or SideStore
    # will treat it as "already installed" and offer no update.
    published = [v["version"] for v in app["versions"]]
    if published:
        highest = max(published, key=version_tuple)
        if version_tuple(args.version) <= version_tuple(highest):
            sys.exit(
                f"refusing to publish {args.version}: not higher than the "
                f"published {highest}. Rollbacks ship old code under a NEW, "
                f"higher version."
            )

    entry = {
        "version": args.version,
        "buildVersion": str(args.build),
        "date": args.date,
        "localizedDescription": args.notes or f"Build {args.version}",
        "downloadURL": args.download_url,
        "size": args.size,
        "minOSVersion": args.min_os,
    }
    # Drop any same-version entry before prepending, so re-runs are idempotent.
    app["versions"] = [v for v in app["versions"] if v["version"] != args.version]
    app["versions"].insert(0, entry)
    del app["versions"][KEEP_VERSIONS:]

    # Legacy v1 mirror of the newest version.
    app["version"] = entry["version"]
    app["versionDate"] = entry["date"]
    app["versionDescription"] = entry["localizedDescription"]
    app["downloadURL"] = entry["downloadURL"]
    app["size"] = entry["size"]
    app["minOSVersion"] = entry["minOSVersion"]

    source_path.write_text(json.dumps(source, indent=2) + "\n")
    print(f"patched {args.bundle_id} -> {args.version} ({args.size} bytes)")


if __name__ == "__main__":
    main()
