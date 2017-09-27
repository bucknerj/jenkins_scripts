#!/bin/bash

jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
up_job_name=$(echo ${this_job_name} | sed -e 's/test/build/')

upstream_dir=$jenkins_jobs_dir/$up_job_name

job_type=$5
if [[ "$job_type" == "cmake" ]]; then
  job_type=$(echo "$this_job_name" | cut -f4 -d'-')
  if [[ "$job_type" == "intel" ]]; then
    job_type=em64t  
  fi
fi

. config/scripts/load_modules.bash $job_type

rm -f inst
ln -sf "$upstream_dir/inst" inst

for i in $(seq 30 -1 1); do
    j=$((i+1))
    if [[ -e previous.$i ]]; then
        rm -rf previous.$j
        rsync -a previous.$i/ previous.$j
    fi
done

if [[ -e previous.1 ]]; then
    rm -rf previous.1
fi

if [[ -e current ]]; then
    rsync -a current/ previous.1
fi

rm -f inst/test/fort.*
rm -f inst/test/scratch/*
rm -f inst/test/output.xml
rm -f inst/test/output.rpt
rm -f inst/test/output/*.out

if [ ! -f output.xfail ]; then
    touch output.xfail
fi

pushd inst/test
ln -sf "$WORKSPACE/output.xfail" output.xfail

if [[ -e "$WORKSPACE/previous.1/output" ]]; then
    ln -sf "$WORKSPACE/previous.1/output" bench
else
    ln -sf "$WORKSPACE/benchmark" bench
fi

sed -e "s%@DIR@%../../config%" \
    "$WORKSPACE/config/data/sccdftb.dat" > sccdftb.dat

charmm_test_vars=$*
./test.com $charmm_test_vars output bench || true
./test.com $charmm_test_vars output bench quantum || true
popd

scl enable rh-python35 bash

/opt/rh/rh-python35/root/usr/bin/python \
  config/scripts/grader.py \
  config/scripts/bad_pats.txt \
  inst/test \
  previous.1/output \
  current/output \
  > inst/test/output.xml

mkdir -p current/output
cp inst/test/output.* current
cp inst/test/output/*.out current/output
