#!/usr/bin/env python3
"""Git gateway MCP server (FastMCP): clone / push / open MR on behalf of coding agents.

The host token lives only in this process (read from a secret file). Agents get
seven narrow tools and never see a credential.

Hardening notes:
- `git_push` never runs git inside the agent-writable work dir. It fetches the
  branch into a gateway-owned bare repo (no agent hooks / config in play) and
  pushes from there.
- Credentials reach git only through the subprocess environment, never argv or
  a stored remote URL, and every output is scrubbed before it is returned.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from fastmcp import FastMCP

CONFIG_PATH = Path(os.environ.get("GATEWAY_CONFIG", "/etc/git-gateway/config.json"))
TOKEN_FILE = Path(os.environ.get("GATEWAY_TOKEN_FILE", "/secrets/token"))
DATA_DIR = Path(os.environ.get("GATEWAY_DATA_DIR", "/var/lib/gw"))
AUDIT_LOG = Path(os.environ.get("GATEWAY_AUDIT_LOG", str(DATA_DIR / "audit.log")))

CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
ALLOWED_ROOT = Path(CFG["allowed_root"]).resolve()
BRANCH_PREFIX = CFG.get("branch_prefix", "demo/")
BRANCH_RE = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/-]{0,120}$")
REPOS: dict[str, dict] = CFG["repos"]
GIT_TIMEOUT = int(CFG.get("git_timeout_seconds", 120))


def _token() -> str:
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


def _scrub(text: str) -> str:
    tok = _token()
    if not tok:
        return text
    b64 = base64.b64encode(f"oauth2:{tok}".encode()).decode()
    for secret in (tok, b64):
        text = text.replace(secret, "***")
    return text


def _audit(event: str, **fields) -> None:
    line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "event": event, **fields}, ensure_ascii=False)
    print(line, file=sys.stderr, flush=True)
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


class GatewayError(Exception):
    pass


def _repo(name: str) -> dict:
    if name not in REPOS:
        raise GatewayError(f"unknown repo {name!r}; allowed: {', '.join(sorted(REPOS))}")
    return REPOS[name]


def _inside_root(path: str, must_exist: bool) -> Path:
    p = Path(path)
    if not p.is_absolute():
        raise GatewayError("path must be absolute")
    resolved = p.resolve()
    if resolved != ALLOWED_ROOT and ALLOWED_ROOT not in resolved.parents:
        raise GatewayError(f"path must be inside {ALLOWED_ROOT}")
    if must_exist and not resolved.exists():
        raise GatewayError(f"path does not exist: {resolved}")
    return resolved


def _branch(branch: str, repo: dict) -> str:
    if not BRANCH_RE.match(branch) or ".." in branch or branch.endswith(("/", ".lock")):
        raise GatewayError("invalid branch name")
    if not branch.startswith(BRANCH_PREFIX):
        raise GatewayError(f"branch must start with {BRANCH_PREFIX!r}")
    if branch == repo.get("default_branch", "main"):
        raise GatewayError("pushing the default branch is not allowed")
    return branch


def _global_config() -> Path:
    """Gateway-owned global config. safe.directory is only honoured from protected config, never from the agent's repo."""
    path = DATA_DIR / "gitconfig"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[safe]\n\tdirectory = *\n", encoding="utf-8")
    return path


def _git_env(authenticated: bool, host_url: str = "") -> dict:
    pairs = [("credential.helper", "")]
    if authenticated:
        auth = base64.b64encode(f"oauth2:{_token()}".encode()).decode()
        origin = host_url.split("/", 3)
        base = "/".join(origin[:3]) + "/"
        pairs.append((f"http.{base}.extraHeader", f"Authorization: Basic {auth}"))
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(DATA_DIR / "home"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(_global_config()),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_COUNT": str(len(pairs)),
    }
    for i, (k, v) in enumerate(pairs):
        env[f"GIT_CONFIG_KEY_{i}"] = k
        env[f"GIT_CONFIG_VALUE_{i}"] = v
    return env


def _git(args: list[str], *, cwd: str | None = None, url: str = "", auth: bool = False) -> str:
    (DATA_DIR / "home").mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(
            ["git", *args], cwd=cwd, env=_git_env(auth, url), capture_output=True,
            text=True, timeout=GIT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise GatewayError(f"git {args[0]} timed out after {GIT_TIMEOUT}s")
    out = _scrub((r.stdout or "") + (r.stderr or "")).strip()
    if r.returncode != 0:
        raise GatewayError(f"git {args[0]} failed: {out[-1500:]}")
    return out


def _api(repo: dict, method: str, path: str, body: dict | None = None):
    base = repo["url"].split("/", 3)
    api = "/".join(base[:3]) + "/api/v4/projects/" + urllib.parse.quote(repo["project"], safe="") + path
    data = urllib.parse.urlencode(body).encode() if body is not None else None
    req = urllib.request.Request(api, data=data, method=method, headers={"PRIVATE-TOKEN": _token()})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except ValueError:
            return e.code, None


def _api_raw(repo: dict, path: str) -> tuple[int, bytes]:
    base = repo["url"].split("/", 3)
    api = "/".join(base[:3]) + "/api/v4/projects/" + urllib.parse.quote(repo["project"], safe="") + path
    req = urllib.request.Request(api, headers={"PRIVATE-TOKEN": _token()})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b""


REF_RE = re.compile(r"^[A-Za-z0-9._/-]{1,200}$")
MAX_READ_BYTES = 200_000


def _ref(ref: str) -> str:
    if not REF_RE.match(ref) or ".." in ref or ref.startswith("-"):
        raise GatewayError("invalid ref")
    return ref


def _repo_path(path: str) -> str:
    path = path.strip("/")
    if ".." in path.split("/") or path.startswith("-") or "\x00" in path:
        raise GatewayError("invalid path")
    return path


def _registry_path() -> Path:
    return DATA_DIR / "clones.json"


def _registry() -> dict:
    try:
        return json.loads(_registry_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _register_clone(d: Path, alias: str) -> None:
    reg = _registry()
    reg[str(d)] = alias
    _registry_path().parent.mkdir(parents=True, exist_ok=True)
    _registry_path().write_text(json.dumps(reg), encoding="utf-8")


def _chown_tree(path: Path, ref: Path) -> None:
    st = ref.stat()
    for root, dirs, files in os.walk(path):
        for name in [""] + dirs + files:
            os.lchown(os.path.join(root, name) if name else root, st.st_uid, st.st_gid)


mcp = FastMCP("git-gateway")


@mcp.tool()
def git_clone(repo: str, dest: str, ref: str = "") -> str:
    """`repo` is the repo alias (e.g. orchestration-demo), never a URL. Clone an allowed repo into `dest` (absolute path under the agent workspace root; must not exist or be empty). Optional `ref` is a branch name to check out instead of the default branch."""
    try:
        r = _repo(repo)
        d = _inside_root(dest, must_exist=False)
        if d.exists() and (not d.is_dir() or any(d.iterdir())):
            raise GatewayError("dest exists and is not an empty directory")
        d.parent.mkdir(parents=True, exist_ok=True)
        args = ["clone", "--no-hardlinks"] + (["--branch", _ref(ref)] if ref else []) + [r["url"], str(d)]
        out = _git(args, url=r["url"], auth=True)
        _chown_tree(d, ALLOWED_ROOT)
        _register_clone(d, repo)
        head = _git(["rev-parse", "HEAD"], cwd=str(d))
        _audit("clone", repo=repo, dest=str(d), ok=True)
        return f"cloned {repo} into {d} at {head}\n{out}"
    except GatewayError as e:
        _audit("clone", repo=repo, dest=dest, ok=False, error=str(e)[:300])
        return f"ERROR: {e}"


@mcp.tool()
def git_push(repo: str, repo_dir: str, branch: str) -> str:
    """`repo` is the repo alias, never a URL. Push a local branch of the repo at `repo_dir` to the remote (branch must start with the allowed prefix; default branch and force pushes are refused)."""
    try:
        r = _repo(repo)
        _branch(branch, r)
        d = _inside_root(repo_dir, must_exist=True)
        if _registry().get(str(d)) != repo:
            raise GatewayError(
                f"{repo_dir} was not created by the git_clone tool for repo {repo!r}. Your current directory is an unrelated checkout and must not be used: "
                f"call git_clone (repo={repo!r}, dest=<a new directory under your working directory>), work and commit inside that directory, then call git_push with that same directory as repo_dir."
            )
        if not (d / ".git").is_dir():
            raise GatewayError("repo_dir is not a git work tree")
        mirror = DATA_DIR / "mirrors" / f"{repo}.git"
        if not mirror.exists():
            mirror.parent.mkdir(parents=True, exist_ok=True)
            _git(["init", "--bare", "-q", str(mirror)])
        _git(["--git-dir", str(mirror), "fetch", "-q", "--no-tags", str(d / ".git"),
              f"+refs/heads/{branch}:refs/heads/{branch}"])
        sha = _git(["--git-dir", str(mirror), "rev-parse", f"refs/heads/{branch}"])
        out = _git(["--git-dir", str(mirror), "push", r["url"], f"refs/heads/{branch}:refs/heads/{branch}"],
                   url=r["url"], auth=True)
        _audit("push", repo=repo, branch=branch, sha=sha, ok=True)
        return f"pushed {branch} at {sha}\n{out}"
    except GatewayError as e:
        _audit("push", repo=repo, branch=branch, ok=False, error=str(e)[:300])
        return f"ERROR: {e}"


@mcp.tool()
def open_mr(repo: str, branch: str, title: str, body: str = "") -> str:
    """`repo` is the repo alias, never a URL. Open a merge request from `branch` into the default branch (never merges). Returns the MR url and number."""
    try:
        r = _repo(repo)
        _branch(branch, r)
        target = r.get("default_branch", "main")
        st, res = _api(r, "POST", "/merge_requests",
                       {"source_branch": branch, "target_branch": target, "title": title, "description": body})
        if st == 409:
            q = urllib.parse.urlencode({"state": "opened", "source_branch": branch, "target_branch": target})
            st2, res2 = _api(r, "GET", "/merge_requests?" + q)
            if st2 == 200 and res2:
                _audit("open_mr", repo=repo, branch=branch, ok=True, existing=True)
                return json.dumps({"url": res2[0]["web_url"], "number": res2[0]["iid"], "existing": True})
        if st not in (200, 201):
            raise GatewayError(f"gitlab {st}: {json.dumps(res)[:500]}")
        _audit("open_mr", repo=repo, branch=branch, ok=True, number=res["iid"])
        return json.dumps({"url": res["web_url"], "number": res["iid"], "existing": False})
    except GatewayError as e:
        _audit("open_mr", repo=repo, branch=branch, ok=False, error=str(e)[:300])
        return f"ERROR: {_scrub(str(e))}"


@mcp.tool()
def mr_status(repo: str, number: int) -> str:
    """`repo` is the repo alias, never a URL. Read-only state of a merge request: open / merged / closed, plus head and merge SHA."""
    try:
        r = _repo(repo)
        st, res = _api(r, "GET", f"/merge_requests/{int(number)}")
        if st != 200:
            raise GatewayError(f"gitlab {st}")
        state = {"opened": "open"}.get(res["state"], res["state"])
        return json.dumps({"number": res["iid"], "state": state, "merged": res["state"] == "merged",
                           "head_sha": res.get("sha"), "merge_sha": res.get("merge_commit_sha"), "url": res["web_url"]})
    except GatewayError as e:
        return f"ERROR: {e}"


@mcp.tool()
def list_branches(repo: str) -> str:
    """`repo` is the repo alias, never a URL. List branch names of an allowed repo (read-only)."""
    try:
        r = _repo(repo)
        st, res = _api(r, "GET", "/repository/branches?per_page=100")
        if st != 200:
            raise GatewayError(f"gitlab {st}")
        return json.dumps([b["name"] for b in res])
    except GatewayError as e:
        return f"ERROR: {e}"


@mcp.tool()
def read_file(repo: str, ref: str, path: str) -> str:
    """`repo` is the repo alias, never a URL. Read-only: return the text of `path` at `ref` (a branch name or a full commit SHA). Use it to read code on the default branch or an artifact pushed by another role."""
    try:
        r = _repo(repo)
        st, body = _api_raw(r, f"/repository/files/{urllib.parse.quote(_repo_path(path), safe='')}/raw?ref={urllib.parse.quote(_ref(ref), safe='')}")
        if st != 200:
            raise GatewayError(f"gitlab {st}: file not found at that ref" if st == 404 else f"gitlab {st}")
        if len(body) > MAX_READ_BYTES:
            raise GatewayError(f"file larger than {MAX_READ_BYTES} bytes")
        _audit("read_file", repo=repo, ref=ref, path=path, ok=True)
        return _scrub(body.decode("utf-8", errors="replace"))
    except GatewayError as e:
        _audit("read_file", repo=repo, ref=ref, path=path, ok=False, error=str(e)[:200])
        return f"ERROR: {e}"


@mcp.tool()
def list_files(repo: str, ref: str, path: str = "") -> str:
    """`repo` is the repo alias, never a URL. Read-only: list files and directories under `path` (default: root) at `ref` (a branch name or a full commit SHA), recursively."""
    try:
        r = _repo(repo)
        q = urllib.parse.urlencode({"ref": _ref(ref), "path": _repo_path(path), "recursive": "true", "per_page": 200})
        st, body = _api_raw(r, "/repository/tree?" + q)
        if st != 200:
            raise GatewayError(f"gitlab {st}")
        items = json.loads(body or b"[]")
        _audit("list_files", repo=repo, ref=ref, path=path, ok=True)
        return json.dumps([f"{i['path']}{'/' if i['type'] == 'tree' else ''}" for i in items])
    except GatewayError as e:
        _audit("list_files", repo=repo, ref=ref, path=path, ok=False, error=str(e)[:200])
        return f"ERROR: {e}"


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.environ.get("GATEWAY_HOST", "127.0.0.1"),
        port=int(os.environ.get("GATEWAY_PORT", "8930")),
        path="/mcp",
        stateless_http=True,
    )
