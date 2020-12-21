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
    tar czf old.tgz old
    rm -rf old
fi

if [[ -f old.tgz ]]; then
  cp old.tgz old.1.tgz
  rm old.tgz
fi

if [[ -e new ]]; then
  tar czf new.tgz new
  rm -rf new
fi

if [[ -f new.tgz ]]; then
  cp new.tgz old.tgz
  rm -rf new.tgz
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

mkdir -p new/output

cp inst/test/output.* new
rm inst/test/output.*

cp inst/test/output/*.out new/output
rm inst/test/output/*.out

tar czf new.tgz new
rm -rf new

if [[ -d xml ]]; then
  rm -rf xml
fi
mkdir xml

/opt/rh/rh-python36/root/usr/bin/python \
  config/scripts/grader.py \
  config/scripts/bad_pats.txt \
  output.xfail \
  inst/test \
  old.tgz \
  new.tgz \
  xml

mkdir -p new/xml
cp xml/*.xml new/xml/
tar rzf new.tgz new/xml
rm -rf new


