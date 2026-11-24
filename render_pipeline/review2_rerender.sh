#!/bin/sh
# Review 2: re-render only the changed images, final quality, one at a time, --resume.
cd "$(dirname "$0")/.."
LIST="119 148 149 103 58 85 143 86 161 44 54 100 41 95 159 114 81 20 57 46 48 99"
for n in $LIST; do
  python render_pipeline/run_batch.py --only "$n" --quality final --resume 2>&1 | grep "^#"
done
# contact sheets (everything is already rendered, so --resume only rebuilds the sheets)
python render_pipeline/run_batch.py --only "$(echo $LIST | tr ' ' ',')" --test review2 --resume | tail -1
for t in "1 1-20" "3 41-60" "5 81-100" "7 101-120" "9 141-160" "10 161"; do
  set -- $t; python render_pipeline/run_batch.py --only "$2" --test "$1" --resume | tail -1
done
echo REVIEW2_DONE
