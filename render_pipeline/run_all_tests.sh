#!/bin/bash
# Final render chain for round 2026-11-06. Restart-safe: re-run this script and
# --resume skips images already rendered at final quality this round.
cd "$(dirname "$0")/.."
for t in "1:1-20" "3:41-60" "5:81-100" "7:101-120" "9:141-160" "10:161"; do
  python render_pipeline/run_batch.py --only "${t#*:}" --test "${t%%:*}" --resume
done
echo "ALL TESTS DONE"
