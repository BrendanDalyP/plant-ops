#!/usr/bin/env bash
# PURPOSE  Print each rule in docs/rules.md with the number of batches that break it in today's file.
# PSEUDOCODE
#   for each table row in docs/rules.md that starts with a rule number:
#       print the number, the rule's name and the expected count (the last column)
#   print how many rules there are
set -euo pipefail
cd "$(dirname "$0")/.."
awk -F'|' '/^\| [0-9]+ \|/ {
    gsub(/^ +| +$/, "", $2); gsub(/^ +| +$/, "", $3); gsub(/^ +| +$/, "", $5)
    printf "%-3s %-45s %s\n", $2, $3, $5; n++
} END { print n " rules" }' docs/rules.md
