#!/usr/bin/env bash
# Runs Claude Code unattended until a deadline, restarting it with fresh context
# whenever a session ends. State carries over in reports/STATUS.md.
# Usage (inside tmux):
#   systemd-inhibit --what=sleep:idle --why="overnight run" scripts/run_overnight.sh 07:00
set -uo pipefail

PROJ="$HOME/SJSU/FALL_2026/CMPE_258/CMPE_258_PROJECT"
PROMPT_FILE="prompts/overnight_01.md"
DEADLINE_HHMM="${1:-07:00}"
cd "$PROJ" || { echo "Project folder missing: $PROJ"; exit 1; }

# Deadline: the next occurrence of HH:MM
END=$(date -d "today $DEADLINE_HHMM" +%s)
[ "$END" -le "$(date +%s)" ] && END=$(date -d "tomorrow $DEADLINE_HHMM" +%s)
DEADLINE_ISO=$(date -d "@$END" -Iseconds)

# Drop any cached sudo credentials so the agent can't use sudo
sudo -k 2>/dev/null || true

# Conda env for every command the agent runs
eval "$(conda shell.bash hook)"
conda activate disasm || { echo "conda env 'disasm' missing; run setup_project.sh"; exit 1; }

# Work on a dated branch, never main
BR="overnight/$(date +%F)"
git switch -c "$BR" 2>/dev/null || git switch "$BR"

mkdir -p logs/overnight reports
RUNLOG=logs/overnight/runner.log
echo "$(date -Is) start, deadline $DEADLINE_ISO, branch $BR" | tee -a "$RUNLOG"

i=0
while [ "$(date +%s)" -lt "$END" ]; do
  if grep -q '^STATE: DONE' reports/STATUS.md 2>/dev/null; then
    echo "$(date -Is) STATUS says DONE; exiting" | tee -a "$RUNLOG"; break
  fi
  i=$((i+1))
  LEFT=$(( END - $(date +%s) ))
  LOG="logs/overnight/session_$(date +%H%M%S)_$i.jsonl"
  START=$(date +%s)
  echo "$(date -Is) session $i starting ($((LEFT/60)) min left) -> $LOG" | tee -a "$RUNLOG"

  timeout "$LEFT" claude -p "$(cat "$PROMPT_FILE")

---
Launch info: DEADLINE=$DEADLINE_ISO. This is session $i of the night.
Read CLAUDE.md, then reports/STATUS.md if it exists, and resume from NEXT ACTION." \
    --dangerously-skip-permissions \
    --output-format stream-json --verbose \
    --max-turns 400 \
    > "$LOG" 2>&1
  RC=$?
  DUR=$(( $(date +%s) - START ))
  echo "$(date -Is) session $i exited rc=$RC after $((DUR/60)) min" | tee -a "$RUNLOG"

  # A session that dies fast is usually a usage limit or network error: back off
  if [ "$DUR" -lt 300 ]; then
    echo "$(date -Is) short session; sleeping 15 min before retry" | tee -a "$RUNLOG"
    sleep 900
  else
    sleep 30
  fi
done

# Last-resort commit, in case the agent ran out of time before committing
git add -A && git commit -qm "overnight run: final autosave" 2>/dev/null || true
git push -u origin "$BR" 2>/dev/null || echo "push failed (check gh auth)" | tee -a "$RUNLOG"
echo "$(date -Is) runner finished" | tee -a "$RUNLOG"
