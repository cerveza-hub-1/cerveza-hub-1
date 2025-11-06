#!/bin/bash

# ---------------------------------------------------------------------------
# Validate commit message against Conventional Commits
# ---------------------------------------------------------------------------

# Get the commit message
COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Regex para Conventional Commits (tipo: feat, fix, chore, docs, style, refactor, perf, test)
REGEX="^(feat|fix|chore|docs|style|refactor|perf|test)(\([a-z0-9_-]+\))?: .+"

if [[ ! $COMMIT_MSG =~ $REGEX ]]; then
  echo "ERROR: Commit message does not follow Conventional Commits!"
  echo "Example of valid commit message:"
  echo "  feat(auth): add login API endpoint"
  echo "  fix(ui): correct button color"
  exit 1
fi

exit 0
