#!/bin/bash

jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
up_job_name=$(echo ${this_job_name} | sed -e 's/test/build/')

upstream_dir=$jenkins_jobs_dir/$up_job_name

job_type=$5
if [[ "$job_type" == "cmake" ]]; then
    job_test=$(echo "$this_job_name" | cut -f4 -d'-')
    if [[ "$job_test" == "intel" ]]; then
        job_type=em64t  
    fi
fi

. config/scripts/load_modules.bash $job_type

rm -f inst
ln -sf "$upstream_dir/inst" inst

for i in $(seq 30 -1 1); do
    j=$((i+1))
    if [[ -e old.$i.tgz ]]; then
      cp old.$i.tgz old.$j.tgz
    fi
done

if [[ -e old ]]; then
    tar czf old.1.tgz old
    rm -rf old
fi

if [[ -e new ]]; then
    mv new old
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
ln -sf "$WORKSPACE/old/output" bench

sed -e "s%@DIR@%../../config%" \
    "$WORKSPACE/config/data/sccdftb.dat" > sccdftb.dat

charmm_test_vars=$*
./test.com $charmm_test_vars output bench || true
popd

mkdir -p new/output
mkdir -p new/xml

/opt/rh/rh-python35/root/usr/bin/python \
  config/scripts/grader.py \
  config/scripts/bad_pats.txt \
  output.xfail \
  inst/test \
  old/output \
  inst/test/output \
  new/xml

cp inst/test/output.* new
cp inst/test/output/*.out new/output
