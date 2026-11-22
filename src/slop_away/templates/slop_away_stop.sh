#!/usr/bin/env bash
set -u

active=$(jq -rse '
  if length != 1 then error("Expected one hook event") else .[0] end
  | if .hook_event_name == "Stop" and (.stop_hook_active | type) == "boolean"
    then .stop_hook_active | tostring
    else error("Invalid stop event") end
') || exit 2
[[ "$active" == true ]] && exit 0
project=${CLAUDE_PROJECT_DIR-}
if [[ "$project" != /* ]]; then
    printf '%s\n' 'slop_away: CLAUDE_PROJECT_DIR needs an absolute path.' >&2
    exit 2
fi
cd -- "$project" || exit 2
slop_away check --output-format agent . >&2
status=$?
[[ $status == 0 ]] && exit 0
exit 2
