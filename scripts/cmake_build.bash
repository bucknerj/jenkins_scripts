#!/bin/bash

jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
if [[ $this_job_name == *stable* ]]; then
    build_type=stable
else
    build_type=${this_job_name:6:3}
fi

up_job_name=''

if [[ "$build_type" == "git" ]]; then
    up_job_name=checkout-charmm
fi

if [[ "$build_type" == "svn" ]]; then
    up_job_name=checkout-dev
fi

if [[ "$build_type" == "bio" ]]; then
    up_job_name=checkout-biovia
fi

if [[ "$build_type" == "stable" ]]; then
    up_job_name=checkout-stable
fi

upstream_dir=$jenkins_jobs_dir/$up_job_name

charmm_build_vars=$*

if [[ "$1" == "--with-intel" ]]; then
    . config/scripts/load_modules.bash em64t
elif [[ "$1" == "--with-pgi" ]]; then
    . config/scripts/load_modules.bash pgi
else
    . config/scripts/load_modules.bash cmake
fi

if [[ -d bld ]]; then
    rm -rf bld;
fi

if [[ -d inst ]]; then
    rm -rf inst;
fi

mkdir bld

pushd bld
if [[ "$1" == "--with-intel" ]]; then
    "$upstream_dir"/configure -p ../inst $charmm_build_vars
elif [[ "$1" == "--with-pgi" ]]; then
    "$upstream_dir"/configure -p ../inst $charmm_build_vars
else
    "$upstream_dir"/configure -p ../inst $charmm_build_vars
fi
make -j4 install
popd
