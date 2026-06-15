#!/usr/bin/env python3
"""Publish this library to the Sideband catalog.

This repo only sends DATA: the raw .SchLib files plus the names/categories from
symbols.yaml. Sideband renders every preview server-side and publishes the
catalog entry — there is no altium-monkey or SVG handling here.

Env:
  SIDEBAND_API_URL        Sideband API base (handles /api/library-publish-source)
  SIDEBAND_CATALOG_URL    Website catalog origin (where the entry is published)
  SIDEBAND_PUBLISH_TOKEN  Publish bearer token
  LIBRARY_SLUG / LIBRARY_TITLE / LIBRARY_DESCRIPTION  (optional overrides)
"""
import json
import os
from pathlib import Path

import requests
import yaml

API = os.environ["SIDEBAND_API_URL"].rstrip("/")
CATALOG = os.environ["SIDEBAND_CATALOG_URL"].rstrip("/")
TOKEN = os.environ["SIDEBAND_PUBLISH_TOKEN"]
SLUG = os.environ.get("LIBRARY_SLUG", "altium-headers")
TITLE = os.environ.get("LIBRARY_TITLE", "Altium Headers & Connectors")
DESCRIPTION = os.environ.get(
    "LIBRARY_DESCRIPTION",
    "Generated pin-header and connector schematic symbols for Altium Designer "
    "(single / dual / angled rows, sockets, boxed IDC, jumpers, terminal blocks).",
)
# Link back to this repo. In GitHub Actions this is derived automatically.
def _source_url():
    if os.environ.get("LIBRARY_SOURCE_URL"):
        return os.environ["LIBRARY_SOURCE_URL"]
    server, repo = os.environ.get("GITHUB_SERVER_URL"), os.environ.get("GITHUB_REPOSITORY")
    return f"{server}/{repo}" if server and repo else "https://github.com/Fermium/altium-library-headers"
SOURCE_URL = _source_url()
# GitHub-style identity (org/repo). Derived from GITHUB_REPOSITORY in CI.
_repo_full = os.environ.get("GITHUB_REPOSITORY", "Fermium/altium-library-headers")
ORG = os.environ.get("LIBRARY_ORG") or (_repo_full.split("/", 1)[0] if "/" in _repo_full else "fermium")
REPO = os.environ.get("LIBRARY_REPO") or (_repo_full.split("/", 1)[1] if "/" in _repo_full else _repo_full)

root = Path(__file__).parent
manifest = yaml.safe_load((root / "symbols.yaml").read_text())

items_meta: dict[str, dict] = {}
paths: list[Path] = []
for entry in manifest.get("symbols", []):
    p = root / entry["file"]
    if not p.exists():
        print(f"  ! missing {entry['file']}")
        continue
    items_meta[p.name] = {"displayName": entry.get("name"), "category": entry.get("category")}
    paths.append(p)

if not paths:
    raise SystemExit("no symbol files found")

spec = {
    "baseUrl": CATALOG,
    "token": TOKEN,
    "slug": SLUG,
    "title": TITLE,
    "org": ORG,
    "repo": REPO,
    "description": DESCRIPTION,
    "sourceUrl": SOURCE_URL,
    "items": items_meta,
}

multipart = [("spec", (None, json.dumps(spec), "application/json"))]
handles = []
for p in paths:
    fh = open(p, "rb")
    handles.append(fh)
    multipart.append(("files", (p.name, fh, "application/octet-stream")))

print(f"Sending {len(paths)} symbols to {API} → catalog {CATALOG} as '{SLUG}' …")
try:
    resp = requests.post(f"{API}/api/library-publish-source", files=multipart, timeout=900)
finally:
    for fh in handles:
        fh.close()

print(resp.status_code, resp.text[:800])
resp.raise_for_status()
