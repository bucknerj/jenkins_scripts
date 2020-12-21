#!/bin/bash

jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
if [[ $this_job_name == *stable* ]]; then
    build_type=stable
elif [[ $this_job_name == *free* ]]; then
    build_type=free
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

if [[ "$build_type" == "free" ]]; then
    up_job_name=checkout-free
fi

upstream_dir=$jenkins_jobs_dir/$up_job_name

charmm_build_vars=$*
source config/scripts/load_modules.bash $1

if [[ -d inst ]]; then
    rm -rf inst;
fi
"$upstream_dir"/tool/NewCharmmTree inst

export MAKE_COMMAND='make -j4 '
pushd inst || exit
./install.com $charmm_build_vars keepf nolog
popd || exit
