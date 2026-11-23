# Record a destructive action as a transcript: what was there, the check of the target, the command, what is there after.
# Source this file from a bash or zsh SCRIPT that performs the action (expect ends the script, so not from an interactive shell):
#
#   source "$S/evidence.sh"   # S: this skill's scripts/ folder
#   evidence_start "$T/destructive/01-old-vm-delete.txt" "Delete the old database VM and its disk" "project shop-prod"
#   note "BEFORE"
#   step gcloud compute instances describe orders-db --format='value(name,status)'
#   expect "disk attached to orders-db" "$(attached_disk orders-db)" "orders-db-disk"
#   note "ACTION"
#   step gcloud compute instances delete orders-db --quiet
#   note "AFTER"
#   step gcloud compute instances list --filter=name=orders-db
#   evidence_end
#
# Run this file directly (bash evidence.sh) to see a sample transcript.

evidence_start() { # <file> <title> [where: host, project, cluster]
  EVIDENCE_FILE=$1
  mkdir -p "$(dirname "$EVIDENCE_FILE")" || return 1
  if [ -s "$EVIDENCE_FILE" ]; then
    # An earlier attempt is evidence too, so it is never overwritten or mixed with a new run.
    echo "evidence_start: $EVIDENCE_FILE already holds a record. Use a new file name for this run." >&2
    return 1
  fi
  exec 3>&1 4>&2
  exec > >(tee -a "$EVIDENCE_FILE") 2>&1
  echo "################ $2"
  echo "# started $(date '+%Y-%m-%d %H:%M:%S %Z') on $(hostname -s)${3:+, $3}"
}

note() { echo; echo "## $*"; }

# Print the command, then run it. The exit status is the command's.
step() { echo; echo "\$ $*"; "$@"; }

# Stop before the action when the target is not the one the plan names: expect <what> <actual> <expected>
expect() {
  if [ "$2" = "$3" ]; then
    echo "OK: $1 is $3"
  else
    echo "REFUSED: $1 is '$2', expected '$3'. Nothing was changed after this line."
    evidence_end
    exit 1
  fi
}

evidence_end() {
  echo; echo "# finished $(date '+%Y-%m-%d %H:%M:%S %Z')"
  exec 1>&3 2>&4 3>&- 4>&-
  # tee is a separate process: one second lets it write the last lines before a caller reads the file.
  command sleep 1
}

if [ -n "${BASH_SOURCE:-}" ] && [ "${BASH_SOURCE[0]}" = "$0" ]; then
  demo=$(mktemp -d) && touch "$demo/volume.img"
  evidence_start "$demo/01-scratch-delete.txt" "Delete the scratch volume" "sample run" || exit 1
  note "BEFORE"; step ls -l "$demo/volume.img"
  expect "file to delete" "$(basename "$demo/volume.img")" "volume.img"
  note "ACTION"; step rm -v "$demo/volume.img"
  note "AFTER"; step ls "$demo"
  evidence_end
  echo "transcript: $demo/01-scratch-delete.txt"
fi
