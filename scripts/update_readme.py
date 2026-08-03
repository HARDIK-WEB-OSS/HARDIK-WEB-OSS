#!/usr/bin/env python3

import os
import sys
import json
import random
import urllib.request
from datetime import datetime, timezone

README_PATH = "README.md"
START_MARKER = "<!--PITSTOP:START-->"
END_MARKER = "<!--PITSTOP:END-->"

USERNAME = os.environ.get("GH_USERNAME", "HARDIK-WEB-OSS")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

API_ROOT = "https://api.github.com"

RADIO_LINES = [
    "\"Box box box, tyres are gone — new PR incoming.\"",
    "\"Gap to the car ahead: one merge conflict.\"",
    "\"Push push push, we need this deploy out.\"",
    "\"That's P1 for the main branch, no issues reported.\"",
    "\"Tyre deg on the legacy code is high, plan the refactor.\"",
    "\"Green means go — pipeline's clean.\"",
    "\"We're losing time in sector 2, check the CI logs.\"",
    "\"Strategy call: ship it and monitor.\"",
]


def api_get(path):
    req = urllib.request.Request(f"{API_ROOT}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def get_user():
    try:
        return api_get(f"/users/{USERNAME}")
    except Exception:
        return {}


def get_latest_event():
    try:
        events = api_get(f"/users/{USERNAME}/events/public")
        for e in events:
            if e.get("type") in ("PushEvent", "PullRequestEvent", "CreateEvent", "IssuesEvent"):
                return e
        return events[0] if events else None
    except Exception:
        return None


def describe_event(e):
    if not e:
        return "No recent telemetry — car's in the garage."
    t = e.get("type", "")
    repo = e.get("repo", {}).get("name", "unknown/repo")
    if t == "PushEvent":
        n = len(e.get("payload", {}).get("commits", []))
        return f"Pushed {n} commit(s) to `{repo}`"
    if t == "PullRequestEvent":
        action = e.get("payload", {}).get("action", "updated")
        return f"{action.capitalize()} a pull request on `{repo}`"
    if t == "CreateEvent":
        ref_type = e.get("payload", {}).get("ref_type", "ref")
        return f"Created a new {ref_type} on `{repo}`"
    if t == "IssuesEvent":
        action = e.get("payload", {}).get("action", "updated")
        return f"{action.capitalize()} an issue on `{repo}`"
    return f"{t} on `{repo}`"


def laps_since_join(user):
    created_at = user.get("created_at")
    if not created_at:
        return None
    joined = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - joined).days


def build_block():
    user = get_user()
    event = get_latest_event()
    laps = laps_since_join(user)
    public_repos = user.get("public_repos", "—")
    followers = user.get("followers", "—")
    radio = random.choice(RADIO_LINES)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("### 🏁 Live Pit Stop")
    lines.append("")
    lines.append("| Telemetry | Reading |")
    lines.append("|---|---|")
    lines.append(f"| 🏎️ Laps on track | {laps if laps is not None else '—'} days since joining GitHub |")
    lines.append(f"| 🔧 Cars in the garage | {public_repos} public repos |")
    lines.append(f"| 📻 Pit crew | {followers} followers |")
    lines.append(f"| 🟢 Last radio call | {describe_event(event)} |")
    lines.append(f"| 🎙️ Team radio | {radio} |")
    lines.append("")
    lines.append(f"<sub>⏱️ Last updated: {now}</sub>")
    return "\n".join(lines)


def main():
    if not os.path.exists(README_PATH):
        print(f"::error::{README_PATH} not found")
        sys.exit(1)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARKER not in content or END_MARKER not in content:
        print(f"::error::Markers {START_MARKER} / {END_MARKER} not found in {README_PATH}")
        sys.exit(1)

    before = content.split(START_MARKER)[0]
    after = content.split(END_MARKER)[1]
    new_block = build_block()

    new_content = f"{before}{START_MARKER}\n{new_block}\n{END_MARKER}{after}"

    if new_content == content:
        print("No change needed.")
        return

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md pit stop section updated.")


if __name__ == "__main__":
    main()