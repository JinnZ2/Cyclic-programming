# fieldlink.py — resolves the cross-repo links declared in .fieldlink.json.
# CC0. stdlib only.
#
# The manifest names sibling repos this one reads data from. Linked data is
# vendored under vendor/<name>/ rather than fetched: the manifest sets
# "offline": true, so nothing here touches the network. A missing source is
# reported, never downloaded — the caller decides what to do about it.
#
# Run `python3 fieldlink.py` to see which links are satisfied.

import fnmatch
import json
import os

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(REPO_ROOT, ".fieldlink.json")


class MissingSource(Exception):
    """A declared source is not vendored locally."""


def load_manifest(path=MANIFEST_PATH):
    """Read .fieldlink.json and return the inner 'fieldlink' mapping."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["fieldlink"]


def get_source(name, manifest=None):
    """Return the source entry named `name`, or None."""
    manifest = manifest or load_manifest()
    for source in manifest.get("sources", []):
        if source.get("name") == name:
            return source
    return None


def resolve(name, path, manifest=None):
    """
    Resolve one declared path within source `name` to an absolute local path.

    Raises MissingSource if the source has no vendored location or the file
    is not there. The message names the upstream repo so the fix is obvious.
    """
    source = get_source(name, manifest)
    if source is None:
        raise MissingSource(f"no source named {name!r} in .fieldlink.json")

    vendored = source.get("vendored")
    if not vendored:
        raise MissingSource(
            f"source {name!r} declares no 'vendored' directory; "
            f"copy {path} from {source.get('repo', 'upstream')}")

    full = os.path.join(REPO_ROOT, vendored, path)
    if not os.path.isfile(full):
        raise MissingSource(
            f"{name}/{path} is not vendored at {full} — copy it from "
            f"{source.get('repo', 'upstream')} (ref {source.get('ref', 'main')})")
    return full


def status(manifest=None):
    """
    Report every declared path as (source_name, path, present, location).

    Glob paths (e.g. "GEIS/**") are reported present when the vendored
    directory contains any match.
    """
    manifest = manifest or load_manifest()
    rows = []
    for source in manifest.get("sources", []):
        name = source.get("name", "?")
        vendored = source.get("vendored")
        for path in source.get("paths", []):
            if not vendored:
                rows.append((name, path, False, None))
                continue
            base = os.path.join(REPO_ROOT, vendored)
            if any(ch in path for ch in "*?["):
                match = _first_glob_match(base, path)
                rows.append((name, path, match is not None, match))
            else:
                full = os.path.join(base, path)
                found = os.path.isfile(full)
                rows.append((name, path, found, full if found else None))
    return rows


def _first_glob_match(base, pattern):
    """First file under base matching pattern, or None. Handles '**'."""
    flat = pattern.replace("**/", "").replace("**", "*")
    for dirpath, _, filenames in os.walk(base):
        rel_dir = os.path.relpath(dirpath, base)
        for filename in filenames:
            rel = filename if rel_dir == "." else os.path.join(rel_dir, filename)
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel, flat):
                return os.path.join(dirpath, filename)
    return None


def component_matrix_path():
    """Absolute path to the vendored repurpose effectiveness matrix."""
    return resolve("component-failure-db", "matrices/repurpose_effectiveness.csv")


def main():
    manifest = load_manifest()
    print(f"fieldlink v{manifest.get('version')} — offline="
          f"{manifest.get('offline')}")
    print("role:", ", ".join(manifest.get("role", [])))
    print()
    rows = status(manifest)
    if not rows:
        print("no sources declared")
        return
    width = max(len(f"{name}/{path}") for name, path, _, _ in rows)
    for name, path, present, location in rows:
        mark = "ok     " if present else "MISSING"
        where = os.path.relpath(location, REPO_ROOT) if location else "-"
        print(f"{mark} {name}/{path:<{width - len(name)}} {where}")
    missing = sum(1 for _, _, present, _ in rows if not present)
    print()
    print(f"{len(rows) - missing}/{len(rows)} sources vendored")


# --- self-test -------------------------------------------------------------

def _t_manifest_loads_and_declares_component_db():
    manifest = load_manifest()
    assert manifest["version"]
    assert get_source("component-failure-db", manifest) is not None


def _t_component_matrix_resolves():
    path = component_matrix_path()
    assert os.path.isfile(path)


def _t_unknown_source_raises():
    try:
        resolve("no-such-source", "x.csv")
    except MissingSource:
        return
    raise AssertionError("expected MissingSource")


def _t_unvendored_source_raises_with_repo_url():
    # geometric-bridge is declared but not vendored, so it must report, not fetch
    try:
        resolve("geometric-bridge", "GEIS/encoder.py")
    except MissingSource as exc:
        assert "github.com" in str(exc)
        return
    raise AssertionError("expected MissingSource")


def _t_status_covers_every_declared_path():
    manifest = load_manifest()
    declared = sum(len(s.get("paths", [])) for s in manifest["sources"])
    assert len(status(manifest)) == declared


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    main()
