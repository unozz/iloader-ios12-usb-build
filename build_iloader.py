#!/usr/bin/env python3
"""Build the reviewed iOS 12 USB patch; never install or launch the result.

Requires an existing Rust toolchain, Bun, Git and Xcode command-line tools.
No account, keychain, pairing-record or device operations are performed here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent
REPO = "https://github.com/nab138/iloader.git"
TAG = "v2.4.0"
COMMIT = "902597564315442f00ab299dcc758ee0e13b8fa8"
UPSTREAM_SHA256 = "38a81529dc87fda47a75d8fc33accab4157040cce4f930cf0608e71fa342edeb"
PATCHED_SHA256 = "e90bdfadbea0133d253d941e35f6053aa872033fb1f32251d3c6297048d27d8c"
RELATIVE_SOURCE = Path("src-tauri/src/pairing.rs")


def run(args, cwd=None, env=None, capture=False):
    return subprocess.run(args, cwd=cwd, env=env, check=True,
                          text=True, capture_output=capture)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check prerequisites only; no downloads")
    args = parser.parse_args()
    tools = {name: shutil.which(name) for name in ("git", "cargo", "rustc", "bun", "xcrun")}
    for name, path in tools.items():
        print(f"{name}: {path or 'MISSING'}", flush=True)
    missing = [name for name, path in tools.items() if not path]
    if missing:
        print("Missing prerequisites. No downloads or installation attempted.", file=sys.stderr)
        return 2
    run([tools["xcrun"], "--find", "clang"], capture=True)
    if args.check:
        print("Prerequisites found; source build and device behavior are not yet verified.")
        return 0

    work = BASE / "Build-iLoader"
    work.mkdir(exist_ok=True)
    source = work / "source"
    if not source.exists():
        run([tools["git"], "clone", "--depth", "1", "--branch", TAG, REPO, str(source)])
    remote = run([tools["git"], "remote", "get-url", "origin"], source, capture=True).stdout.strip()
    if remote != REPO:
        raise RuntimeError("Unexpected source origin; existing files were preserved.")
    head = run([tools["git"], "rev-parse", "HEAD"], source, capture=True).stdout.strip()
    tag_head = run([tools["git"], "rev-parse", TAG + "^{commit}"], source, capture=True).stdout.strip()
    if head != tag_head or head != COMMIT:
        raise RuntimeError("Unexpected source revision; existing files were preserved.")
    pairing = source / RELATIVE_SOURCE
    digest = hashlib.sha256(pairing.read_bytes()).hexdigest()
    if digest not in (UPSTREAM_SHA256, PATCHED_SHA256):
        raise RuntimeError("Pairing source differs from the reviewed version; no patch applied.")
    changed = run([tools["git"], "diff", "HEAD", "--name-only"], source, capture=True).stdout.splitlines()
    allowed = [] if digest == UPSTREAM_SHA256 else [RELATIVE_SOURCE.as_posix()]
    if changed != allowed:
        raise RuntimeError("Unexpected source edits; no files overwritten.")
    if digest == UPSTREAM_SHA256:
        patch = str(BASE / "iloader-v2.4.0-legacy-usb.patch")
        run([tools["git"], "apply", "--check", patch], source)
        run([tools["git"], "apply", patch], source)
    if hashlib.sha256(pairing.read_bytes()).hexdigest() != PATCHED_SHA256:
        raise RuntimeError("Patched source verification failed.")

    env = os.environ.copy()
    env["CARGO_BUILD_JOBS"] = "1"
    env["CARGO_TARGET_DIR"] = str(work / "target")
    # Only create an app inside the workspace. No updater signing key required.
    # Keep the upstream identifier; no account/storage settings are modified.
    config = {"productName": "iloader iOS12 USB", "bundle": {"createUpdaterArtifacts": False}}
    config_path = work / "build-config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    run([tools["bun"], "install", "--frozen-lockfile"], source, env)
    run([tools["bun"], "run", "tauri", "build", "--bundles", "app",
         "--config", str(config_path)], source, env)
    apps = list((work / "target/release/bundle/macos").glob("*.app"))
    if len(apps) != 1:
        raise RuntimeError("Expected one built app; inspect build output.")
    print(f"Built locally: {apps[0]}")
    print("Not installed or launched. USB connection and IPA installation remain unverified.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Build stopped: {error}", file=sys.stderr)
        sys.exit(1)
