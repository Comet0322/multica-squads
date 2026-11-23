#!/usr/bin/env bash
# Open a pull request on GitHub, or replace an open one's body. Usage:
#   github-pr.sh <repo> <head-branch> <base-branch> <title> <body-file>
#   github-pr.sh --update <repo> <head-branch> <body-file>   (prints the URL, or
#                                                             'none' if no PR is open)
# <repo> is `owner/name`, or just `name` (owner then defaults to the logged-in `gh` user).
# A later ticket's commits land on an open PR by themselves, but its body does not:
# --update rewrites the body of the open PR whose head is <head-branch>, which is how
# a criterion added after the PR was opened reaches the one artefact a human reads.
# Authenticates through `gh` (its own stored login; nothing is printed). Prints the PR URL.
set -euo pipefail
resolve() { case "$1" in */*) echo "$1";; *) echo "$(gh api user -q .login)/$1";; esac; }

if [ "${1:-}" = "--update" ]; then
  repo=$(resolve "$2"); head="$3"; body_file="$4"
  num=$(gh pr list -R "$repo" --state open --head "$head" --json number -q '.[0].number // empty')
  # No open PR is a normal answer, not a failure: the caller is told to try --update
  # first on every run, so a non-zero exit here would put a failing command on the
  # ordinary path -- at the terminal step, where the leader has no further wake coming.
  [ -n "$num" ] || { echo "none"; exit 0; }
  gh pr edit "$num" -R "$repo" --body-file "$body_file" >/dev/null
  gh pr view "$num" -R "$repo" --json url -q .url
  exit 0
fi

repo=$(resolve "$1"); head="$2"; base="$3"; title="$4"; body_file="$5"
gh pr create -R "$repo" --head "$head" --base "$base" --title "$title" --body-file "$body_file"
