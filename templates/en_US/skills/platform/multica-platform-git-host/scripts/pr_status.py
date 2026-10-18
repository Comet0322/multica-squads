#!/usr/bin/env python3
"""Read the state of a pull request / merge request. Read-only.

Prints one JSON line: {"number": N, "state": "open|merged|closed", "merged": bool,
"head_sha": "...", "merge_sha": "...|null", "url": "..."}.
Supported config.yaml `type`: forgejo (also Gitea), gitlab, azure.
Python 3.9+, stdlib only. Reuses the helpers of open_pr.py.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from open_pr import load_config, parse_remote, request  # noqa: E402


def forgejo(scheme, host, path, n, token):
    base = "%s://%s/api/v1/repos/%s/pulls/%s" % (scheme, host, path, n)
    st, r = request("GET", base, {"Authorization": "token " + token})
    if st != 200:
        raise SystemExit("forgejo %s: %s" % (st, r))
    merged = bool(r.get("merged"))
    return {"number": r["number"], "state": "merged" if merged else r["state"], "merged": merged,
            "head_sha": r["head"]["sha"], "merge_sha": r.get("merge_commit_sha"), "url": r["html_url"]}


def gitlab(scheme, host, path, n, token):
    base = "%s://%s/api/v4/projects/%s/merge_requests/%s" % (scheme, host, urllib.parse.quote(path, safe=""), n)
    st, r = request("GET", base, {"PRIVATE-TOKEN": token})
    if st != 200:
        raise SystemExit("gitlab %s: %s" % (st, r))
    merged = r["state"] == "merged"
    return {"number": r["iid"], "state": "open" if r["state"] == "opened" else r["state"], "merged": merged,
            "head_sha": r.get("sha"), "merge_sha": r.get("merge_commit_sha"), "url": r["web_url"]}


def azure(scheme, host, path, n, token):
    if "/_git/" not in path:
        raise SystemExit("azure: remote URL must look like <org>/<project>/_git/<repo>, got " + path)
    prefix, repo = path.split("/_git/", 1)
    web = "%s://%s/%s" % (scheme, host, prefix)
    api = "%s/_apis/git/repositories/%s/pullrequests/%s?api-version=7.1" % (web, repo, n)
    st, r = request("GET", api, {"Authorization": "Basic " + base64.b64encode((":" + token).encode()).decode()})
    if st != 200:
        raise SystemExit("azure %s: %s" % (st, r))
    state = {"active": "open", "completed": "merged", "abandoned": "closed"}.get(r["status"], r["status"])
    return {"number": r["pullRequestId"], "state": state, "merged": state == "merged",
            "head_sha": r["lastMergeSourceCommit"]["commitId"],
            "merge_sha": (r.get("lastMergeCommit") or {}).get("commitId"),
            "url": "%s/_git/%s/pullrequest/%d" % (web, repo, r["pullRequestId"])}


PROVIDERS = {"forgejo": forgejo, "gitea": forgejo, "gitlab": gitlab, "azure": azure}


def main():
    cfg = load_config()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--number", required=True, help="PR / MR number")
    ap.add_argument("--repo-url", help="default: `git remote get-url origin` in cwd")
    ap.add_argument("--type", default=os.environ.get("GIT_HOST_TYPE") or cfg.get("type"))
    a = ap.parse_args()
    if a.type not in PROVIDERS:
        sys.exit("BLOCKED: git host type %r unset/unsupported (config.yaml `type`: %s)" % (a.type, "/".join(PROVIDERS)))
    token_env = cfg.get("token_env", "GIT_HOST_TOKEN")
    token = os.environ.get(token_env, "")
    if not token:
        sys.exit("BLOCKED: env %s is empty" % token_env)
    url = a.repo_url or subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    scheme, host, path = parse_remote(url)
    print(json.dumps(PROVIDERS[a.type](scheme, host, path, a.number, token), ensure_ascii=False))


if __name__ == "__main__":
    main()
