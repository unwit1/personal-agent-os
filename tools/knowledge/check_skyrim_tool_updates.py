#!/usr/bin/env python3
"""Check watched Skyrim tooling repositories for upstream changes.

This produces a *candidate* snapshot. It never edits canonical compatibility claims.
Set GITHUB_TOKEN to reduce rate limits for private/high-frequency use.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/"knowledge/libraries/skyrim-modding/automation/ai-tool-watchlist.json"

def request(url):
    headers={"Accept":"application/vnd.github+json","User-Agent":"personal-agent-os-skyrim-tool-watch"}
    token=os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"]=f"Bearer {token}"
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=30) as response:
        return json.load(response)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--watchlist",type=Path,default=DEFAULT)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    watch=json.loads(args.watchlist.read_text(encoding="utf-8"))
    rows=[]
    for item in watch["projects"]:
        repo=item["repository"]
        row=dict(item)
        try:
            meta=request(f"https://api.github.com/repos/{repo}")
            row.update({
                "default_branch":meta.get("default_branch"),
                "pushed_at":meta.get("pushed_at"),
                "updated_at":meta.get("updated_at"),
                "license":(meta.get("license") or {}).get("spdx_id"),
                "archived":meta.get("archived"),
                "html_url":meta.get("html_url"),
            })
            try:
                rel=request(f"https://api.github.com/repos/{repo}/releases/latest")
                row["latest_release"]={
                    "tag":rel.get("tag_name"),
                    "published_at":rel.get("published_at"),
                    "prerelease":rel.get("prerelease"),
                    "url":rel.get("html_url"),
                }
            except Exception as exc:
                row["latest_release_error"]=str(exc)
        except Exception as exc:
            row["error"]=str(exc)
        rows.append(row)
    payload={
        "schema_version":"skyrim-tool-watch-snapshot-v1",
        "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "projects":rows,
        "policy":"candidate evidence only; compare/diff then review before canonical promotion"
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(f"Checked {len(rows)} repositories -> {args.output}")

if __name__=="__main__":
    main()
