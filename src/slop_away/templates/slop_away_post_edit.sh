#!/usr/bin/env bash
set -u

event=$(cat) || exit 2
mapfile -d '' -t fields < <(jq -jse '
  if length != 1 then error("Expected one hook event") else .[0] end
  | if .hook_event_name == "PostToolUse"
    and (.tool_name == "Write" or .tool_name == "Edit")
    and all([.cwd, .tool_input.file_path][];
      type == "string" and length > 0 and (contains("\u0000") | not))
    then [.cwd, .tool_input.file_path][] | ., "\u0000"
    else error("Invalid post-edit event") end
' <<< "$event")
if [[ ${#fields[@]} != 2 || "${fields[0]}" != /* ]]; then
    printf '%s\n' 'slop_away: Invalid post-edit event.' >&2
    exit 2
fi
file=${fields[1]}
[[ "$file" == *.md ]] || exit 0
if [[ "$file" != /* ]]; then
    file="${fields[0]}/$file"
fi
project=${CLAUDE_PROJECT_DIR-}
if [[ "$project" != /* ]]; then
    printf '%s\n' 'slop_away: CLAUDE_PROJECT_DIR needs an absolute path.' >&2
    exit 2
fi
cd -- "$project" || exit 2
slop_away check --force-exclude --output-format agent -- "$file" >&2
status=$?
[[ $status == 0 ]] && exit 0
exit 2
