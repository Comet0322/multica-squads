#!/usr/bin/env python3
"""Open a pull request / merge request on the repo's git host. Never merges.

Supported config.yaml `type`: forgejo (also Gitea), gitlab, azure.
Python 3.9+, stdlib only. Token comes from the env var named by `token_env`.
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    """Flat `key: value` reader for ../config.yaml (no PyYAML dependency)."""
    cfg = {}
    path = os.path.join(HERE, "..", "config.yaml")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if ":" in line:
                    k, v = line.split(":", 1)
                    cfg[k.strip()] = v.strip().strip("\"'")
    return cfg


def parse_remote(url):
    """Return (scheme, host, path) with credentials stripped; path has no .git."""
    m = re.match(r"^(?:ssh://)?git@([^:/]+)[:/](.+)$", url)
    if m:
        scheme, host, path = "https", m.group(1), m.group(2)
        if host == "ssh.dev.azure.com":  # git@ssh.dev.azure.com:v3/org/project/repo
            host = "dev.azure.com"
            org, project, repo = path[len("v3/"):].split("/", 2)
            path = "%s/%s/_git/%s" % (org, project, repo)
    else:
        p = urllib.parse.urlparse(url)
        scheme, host, path = p.scheme, p.hostname + (":%d" % p.port if p.port else ""), p.path.lstrip("/")
    return scheme, host, re.sub(r"\.git$", "", path).strip("/")


def request(method, url, headers, payload=None, form=False):
    data = None
    if payload is not None:
        if form:
            data = urllib.parse.urlencode(payload).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, {"message": body[:500]}


def forgejo(scheme, host, path, a, token):
    base = "%s://%s/api/v1/repos/%s" % (scheme, host, path)
    h = {"Authorization": "token " + token}
    body = {"title": a.title, "head": a.head, "base": a.base, "body": a.body}
    if a.dry_run:
        return {"method": "POST", "url": base + "/pulls", "body": body}
    st, r = request("POST", base + "/pulls", h, body)
    if st in (409, 422):  # PR for this head already exists -> reuse it
        st2, r2 = request("GET", "%s/pulls/%s/%s" % (base, urllib.parse.quote(a.base, safe=""),
                                                  urllib.parse.quote(a.head, safe="")), h)
        if st2 == 200:
            return {"url": r2["html_url"], "number": r2["number"], "existing": True}
    if st not in (200, 201):
        raise SystemExit("forgejo %s: %s" % (st, r))
    return {"url": r["html_url"], "number": r["number"], "existing": False}


def gitlab(scheme, host, path, a, token):
    base = "%s://%s/api/v4/projects/%s/merge_requests" % (scheme, host, urllib.parse.quote(path, safe=""))
    h = {"PRIVATE-TOKEN": token}
    form = {"source_branch": a.head, "target_branch": a.base, "title": a.title, "description": a.body}
    if a.dry_run:
        return {"method": "POST", "url": base, "body": form}
    st, r = request("POST", base, h, form, form=True)
    if st == 409:  # already exists -> look it up
        q = urllib.parse.urlencode({"state": "opened", "source_branch": a.head, "target_branch": a.base})
        st2, r2 = request("GET", base + "?" + q, h)
        if st2 == 200 and r2:
            return {"url": r2[0]["web_url"], "number": r2[0]["iid"], "existing": True}
    if st not in (200, 201):
        raise SystemExit("gitlab %s: %s" % (st, r))
    return {"url": r["web_url"], "number": r["iid"], "existing": False}


def azure(scheme, host, path, a, token):
    if "/_git/" not in path:
        raise SystemExit("azure: remote URL must look like <org>/<project>/_git/<repo>, got " + path)
    prefix, repo = path.split("/_git/", 1)
    web = "%s://%s/%s" % (scheme, host, prefix)  # <collection or org>/<project>
    api = "%s/_apis/git/repositories/%s/pullrequests" % (web, repo)
    h = {"Authorization": "Basic " + base64.b64encode((":" + token).encode()).decode()}
    body = {"sourceRefName": "refs/heads/" + a.head, "targetRefName": "refs/heads/" + a.base,
            "title": a.title, "description": a.body}
    if a.dry_run:
        return {"method": "POST", "url": api + "?api-version=7.1", "body": body}
    st, r = request("POST", api + "?api-version=7.1", h, body)
    if st == 409 or (st == 400 and "already" in json.dumps(r).lower()):
        q = urllib.parse.urlencode({"searchCriteria.sourceRefName": body["sourceRefName"],
                                    "searchCriteria.targetRefName": body["targetRefName"],
                                    "searchCriteria.status": "active", "api-version": "7.1"})
        st2, r2 = request("GET", api + "?" + q, h)
        if st2 == 200 and r2.get("value"):
            n = r2["value"][0]["pullRequestId"]
            return {"url": "%s/_git/%s/pullrequest/%d" % (web, repo, n), "number": n, "existing": True}
    if st not in (200, 201):
        raise SystemExit("azure %s: %s" % (st, r))
    n = r["pullRequestId"]
    return {"url": "%s/_git/%s/pullrequest/%d" % (web, repo, n), "number": n, "existing": False}


PROVIDERS = {"forgejo": forgejo, "gitea": forgejo, "gitlab": gitlab, "azure": azure}


def main():
    cfg = load_config()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--head", required=True, help="source (delivery) branch")
    ap.add_argument("--base", default=cfg.get("default_base", "main"))
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", help="file holding the PR description (default: empty)")
    ap.add_argument("--repo-url", help="default: `git remote get-url origin` in cwd")
    ap.add_argument("--type", default=os.environ.get("GIT_HOST_TYPE") or cfg.get("type"))
    ap.add_argument("--dry-run", action="store_true", help="print the request, send nothing")
    a = ap.parse_args()

    if a.type not in PROVIDERS:
        sys.exit("BLOCKED: git host type %r unset/unsupported (config.yaml `type`: %s)" % (a.type, "/".join(PROVIDERS)))
    url = a.repo_url or subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    a.body = open(a.body_file, encoding="utf-8").read() if a.body_file else ""
    token_env = cfg.get("token_env", "GIT_HOST_TOKEN")
    token = os.environ.get(token_env, "")
    if not token and not a.dry_run:
        sys.exit("BLOCKED: env %s is empty (token with permission to open PRs only)" % token_env)
    scheme, host, path = parse_remote(url)
    print(json.dumps(PROVIDERS[a.type](scheme, host, path, a, token), ensure_ascii=False))


if __name__ == "__main__":
    main()
