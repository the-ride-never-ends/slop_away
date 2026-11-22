#!/usr/bin/env bash
set -u

event=$(cat) || exit 2
mapfile -d '' -t fields < <(jq -jse '
  if length != 1 then error("Expected one hook event") else .[0] end
  | if .hook_event_name == "PreToolUse" and .tool_name == "Bash"
    and (.tool_input.command | type) == "string"
    and (.tool_input.command | contains("\u0000") | not)
    then .tool_input.command, "\u0000"
    else error("Invalid pre-bash event") end
' <<< "$event")
if [[ ${#fields[@]} != 1 ]]; then
    printf '%s\n' 'slop_away: Invalid pre-bash event.' >&2
    exit 2
fi
slop_away guard -- "${fields[0]}"
status=$?
[[ $status == 0 ]] && exit 0
exit 2
