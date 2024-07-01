#!/bin/bash

jenkins_jobs_dir=$(dirname $(dirname "$WORKSPACE"))
this_job_name=$(basename $(dirname "$WORKSPACE"))

up_job_name=${this_job_name%.*}.test
up_dir=$jenkins_jobs_dir/$up_job_name/workspace
up_charmm=$up_dir/inst
sedprogs=$up_charmm/test/seddir

test_date_raw=$(head -1 $up_dir/current/output.rpt | awk '{print $2" "$3" "$6}')
test_date=$(date -d"$test_date_raw" +%Y.%m.%d)

if [[ ! -e tests/$test_date ]]; then
  mkdir -p tests/"$test_date"
fi

for fn in $(ls $up_dir/current/output/*.out); do 
  fname=$(basename $fn)
  tname=${fname%.*}
  cno=$(basename $(dirname $(ls $up_charmm/test/c??test/$tname.inp)))
  sed -e '1,10d' $fn | sed -f "$sedprogs" > tests/$test_date/$cno.$tname
done

for d in $(ls -d $up_dir/previous.*); do 
  if [[ ! -e $d/output.rpt ]]; then
    continue
  fi
  old_date_raw=$(head -1 $d/output.rpt | awk '{print $2" "$3" "$6}')
  old_date=$(date -d"$old_date_raw" +%Y.%m.%d)
  if [[ ! -e tests/$old_date ]]; then
    mkdir -p tests/"$old_date"
    for fn in $(ls $d/output/*.out); do 
      fname=$(basename $fn)
      tname=${fname%.*}
      cno=$(basename $(dirname $(ls $up_charmm/test/c??test/$tname.inp)))
      sed -e '1,10d' $fn | sed -f "$sedprogs" > tests/$old_date/$cno.$tname
    done
  fi
done

if [[ ! -e results/$test_date ]]; then
  mkdir -p "results/$test_date/tables" "results/$test_date/images"
fi

table_dir=$WORKSPACE/results/$test_date/tables
score_table=$table_dir/scores.txt

pushd tests
output_dirs=$(ls -d 20??.??.?? | tail -30 | tr '\n' ' ')
/usr/bin/guile -e main -s $WORKSPACE/scripts/diffall.scm $output_dirs > "$score_table"
popd

img_dir=$WORKSPACE/results/$test_date/images
prefixes=$(cut -f1 -d'.' "$score_table" | sort | uniq)
for prefix in $prefixes; do
  grep "$prefix" "$score_table" > "$table_dir/$prefix.txt"
  /usr/bin/Rscript scripts/heatmap.R \
    "$table_dir/$prefix.txt" \
    "$img_dir/$prefix.png"
done

pushd $WORKSPACE/results
if [[ -e current ]]; then
  rm current
fi
ln -fs $test_date current
popd
