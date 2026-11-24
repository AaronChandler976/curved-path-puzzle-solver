#!/usr/bin/env bash
# Runs Claude Code unattended until a deadline, restarting it with fresh context
# whenever a session ends. State carries over in <run_dir>/STATUS.md.
# Usage (inside tmux):
#   systemd-inhibit --what=sleep:idle --why="claude run" scripts/run_overnight.sh <HH:MM | "YYYY-MM-DD HH:MM"> <prompt.md> <run_dir>
# Example:
#   systemd-inhibit --what=sleep:idle --why="claude run" scripts/run_overnight.sh 22:00 prompts/run_02.md reports/run02
set -uo pipefail

PROJ="$HOME/SJSU/FALL_2026/CMPE_258/CMPE_258_PROJECT"
DEADLINE_HHMM="${1:-07:00}"
PROMPT_FILE="${2:-prompts/overnight_01.md}"
RUN_DIR="${3:-reports}"
cd "$PROJ" || { echo "Project folder missing: $PROJ"; exit 1; }
[ -f "$PROMPT_FILE" ] || { echo "Prompt file missing: $PROMPT_FILE"; exit 1; }
mkdir -p logs/overnight "$RUN_DIR"

# Only one runner at a time (run 01 accidentally started three)
exec 9>logs/runner.lock
flock -n 9 || { echo "Another runner is already running. Stop it first: pkill -f run_overnight.sh"; exit 1; }

# Deadline: "HH:MM" = the next occurrence of that time; "YYYY-MM-DD HH:MM" = that exact time (multi-day runs)
if [[ "$DEADLINE_HHMM" == *-* ]]; then
  END=$(date -d "$DEADLINE_HHMM" +%s) || { echo "Bad deadline: $DEADLINE_HHMM"; exit 1; }
  [ "$END" -le "$(date +%s)" ] && { echo "Deadline is in the past: $DEADLINE_HHMM"; exit 1; }
else
  END=$(date -d "today $DEADLINE_HHMM" +%s)
  [ "$END" -le "$(date +%s)" ] && END=$(date -d "tomorrow $DEADLINE_HHMM" +%s)
fi
DEADLINE_ISO=$(date -d "@$END" -Iseconds)

# Drop any cached sudo credentials so the agent can't use sudo
sudo -k 2>/dev/null || true

# Conda env; ROS's PYTHONPATH breaks pytest/imports, so drop it
set +u
eval "$(conda shell.bash hook)"
conda activate disasm || { echo "conda env 'disasm' missing"; exit 1; }
set -u
unset PYTHONPATH

# Each run gets its own branch, started from wherever you are now
RUN_NAME=$(basename "$RUN_DIR")
BR="run/$(date +%F)-$RUN_NAME"
git switch -c "$BR" 2>/dev/null || git switch "$BR"

RUNLOG="logs/overnight/runner_${RUN_NAME}.log"
echo "$(date -Is) start: prompt=$PROMPT_FILE run_dir=$RUN_DIR deadline=$DEADLINE_ISO branch=$BR power=$(powerprofilesctl get 2>/dev/null || echo unknown)" | tee -a "$RUNLOG"

i=0
while [ "$(date +%s)" -lt "$END" ]; do
  if grep -q '^STATE: DONE' "$RUN_DIR/STATUS.md" 2>/dev/null; then
    echo "$(date -Is) $RUN_DIR/STATUS.md says DONE; exiting" | tee -a "$RUNLOG"; break
  fi
  i=$((i+1))
  LEFT=$(( END - $(date +%s) ))
  LOG="logs/overnight/${RUN_NAME}_session_$(date +%H%M%S)_$i.jsonl"
  START=$(date +%s)
  echo "$(date -Is) session $i starting ($((LEFT/60)) min left) -> $LOG" | tee -a "$RUNLOG"

  timeout "$LEFT" claude -p "$(cat "$PROMPT_FILE")

---
Launch info: DEADLINE=$DEADLINE_ISO. RUN_DIR=$RUN_DIR. This is session $i of this run.
Read CLAUDE.md and docs/PLAN.md, then $RUN_DIR/STATUS.md if it exists, and resume from NEXT ACTION." \
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

git add -A && git commit -qm "$RUN_NAME: final autosave" 2>/dev/null || true
git push -u origin "$BR" 2>/dev/null || echo "push failed (check gh auth)" | tee -a "$RUNLOG"
echo "$(date -Is) runner finished" | tee -a "$RUNLOG"
