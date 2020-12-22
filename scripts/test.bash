#!/bin/bash

jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
up_job_name=${this_job_name//test/build}

upstream_dir=$jenkins_jobs_dir/$up_job_name

job_type=gnu
if [[ $this_job_name == *"intel"* ]]; then
    job_type=em64t  
elif [[ $this_job_name == *"cmake"* ]]; then
    job_type=cmake
elif [[ $this_job_name == *"dev"* ]]; then
    job_type=cmake
elif [[ $this_job_name == *"gcc"* ]]; then
    job_type=gcc
elif [[ $this_job_name == *"pgi"* ]]; then
    job_type=pgi
fi

. config/scripts/load_modules.bash $job_type

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
ln -sf "$WORKSPACE/output.xfail" output.xfail

sed -e "s%@DIR@%../../config%" \
    "$WORKSPACE/config/data/sccdftb.dat" > sccdftb.dat

charmm_test_vars=$*
./test.com $charmm_test_vars output || true
popd || exit

mkdir -p results/output

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

if [[ $job_type == gcc ]]; then
    dev_dir=${WORKSPACE//-gcc-/-dev-}
    /opt/rh/rh-python36/root/usr/bin/python \
	config/scripts/grader.py \
	config/scripts/bad_pats.txt \
	output.xfail \
	inst/test \
	$dev_dir/new.tgz \
	new.tgz \
	xml
else
    /opt/rh/rh-python36/root/usr/bin/python \
	config/scripts/grader.py \
	config/scripts/bad_pats.txt \
	output.xfail \
	inst/test \
	old.tgz \
	new.tgz \
	xml
fi

if [[ -d config ]]; then
  rm -rf config
fi
