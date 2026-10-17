#!/usr/bin/env python3
"""Talk to a Multica agent in chat mode via the REST API (the CLI has no chat send).

Usage: tools/chat.py <agent-name> "<message>" [--session ID] [--wait SECONDS]
Prints the session id and the agent's reply. Reuse --session for follow-ups.
"""
import argparse, json, subprocess, time, urllib.request
from pathlib import Path

cfg = json.loads((Path.home() / ".multica/config.json").read_text())


def call(method, path, body=None):
    req = urllib.request.Request(cfg["server_url"] + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + cfg["token"], "X-Workspace-ID": cfg["workspace_id"],
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        out = r.read()
        return json.loads(out) if out else None


ap = argparse.ArgumentParser()
ap.add_argument("agent"); ap.add_argument("message")
ap.add_argument("--session"); ap.add_argument("--wait", type=int, default=240)
a = ap.parse_args()

agents = json.loads(subprocess.run(["multica", "agent", "list", "--output", "json"],
                                   capture_output=True, text=True, check=True).stdout)
agent = next(x for x in agents if x["name"] == a.agent and not x.get("archived_at"))
sid = a.session or call("POST", "/api/chat/sessions", {"agent_id": agent["id"]})["id"]
before = call("GET", f"/api/chat/sessions/{sid}/messages") or []
n = len(before if isinstance(before, list) else before.get("messages", []))
call("POST", f"/api/chat/sessions/{sid}/messages", {"content": a.message})
print("session:", sid)
end = time.time() + a.wait
while time.time() < end:
    time.sleep(5)
    msgs = call("GET", f"/api/chat/sessions/{sid}/messages")
    msgs = msgs if isinstance(msgs, list) else msgs.get("messages", [])
    new = [m for m in msgs[n:] if m.get("role") == "assistant"]
    if new and not call("GET", f"/api/chat/sessions/{sid}/pending-task").get("task_id"):
        print(new[-1]["content"]); break
else:
    print("timeout waiting for reply")
