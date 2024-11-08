#!/bin/bash

charmm_test_vars=$*
jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
up_job_name=${this_job_name//test/build}

upstream_dir=$jenkins_jobs_dir/$up_job_name

job_type=gcc
if [[ $this_job_name == *"intel"* ]]; then
    job_type=intel
fi

. scripts/load_modules.bash $job_type

rm -f inst
ln -sf "$upstream_dir/inst" inst

for i in $(seq 5 -1 1); do
    j=$((i+1))
    if [[ -e old.$i.tgz ]]; then
      cp "old.$i.tgz" "old.$j.tgz"
    fi
done

if [[ -e old ]]; then
  cp -r old results
  tar czf old.tgz results
  rm -rf old results
fi

if [[ -f old.tgz ]]; then
  cp old.tgz old.1.tgz
  rm -f old.tgz
fi

if [[ -e new ]]; then
  cp -r new results
  tar czf new.tgz results
  rm -rf new results
fi

if [[ -f new.tgz ]]; then
  cp new.tgz old.tgz
  rm -f new.tgz
fi

rm -f inst/test/fort.*
rm -f inst/test/scratch/*
rm -f inst/test/output.xml
rm -f inst/test/output.rpt
rm -f inst/test/output/*.out

if [ ! -f output.xfail ]; then
  touch output.xfail
fi

pushd inst/test || exit

if [[ -e old ]]; then
    rm -rf old
fi

if [[ -f "$WORKSPACE/old.tgz" ]]; then
    tar xzf "$WORKSPACE/old.tgz"
    cp -r results old
    rm -rf results
fi

ln -sf "$WORKSPACE/output.xfail" output.xfail

ln -sf '/home/bucknerj/src/jenkins/sccdftb_data/sccdftb.dat' sccdftb.dat

sed '/limit filesize/d' ./test.com > test2.com
/usr/bin/tcsh ./test2.com $charmm_test_vars output old/output | tee test.log || true
CMPDIR=old/output/ ../tool/Compare out put &> compare.log
popd || exit

mkdir -p results/output

cp inst/test/test.log results
rm inst/test/test.log

cp inst/test/compare.log results
rm inst/test/compare.log

cp inst/test/output.* results
rm inst/test/output.*

cp inst/test/output/*.out results/output
rm inst/test/output/*.out

tar czf new.tgz results
rm -rf results

if [[ -d xml ]]; then
  rm -rf xml
fi
mkdir xml

/usr/bin/python \
    scripts/grader.py \
    scripts/bad_pats.txt \
    output.xfail \
    inst/test \
    old.tgz \
    new.tgz \
    xml

if [[ -d scripts ]]; then
  rm -rf scripts
fi
