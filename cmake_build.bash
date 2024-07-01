#!/bin/bash

jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
if [[ $this_job_name == *stable* ]]; then
    build_type=stable
elif [[ $this_job_name == *free* ]]; then
    build_type=free
elif [[ $this_job_name == *gcc* ]]; then
    build_type=gcc
else
    build_type=${this_job_name:6:3}
fi

echo "build type ${build_type}"

up_job_name=''

if [[ "$build_type" == "git" ]]; then
    up_job_name=checkout-charmm
elif [[ "$build_type" == "ber" ]]; then
    up_job_name=checkout-ber
elif [[ "$build_type" == "dev" ]]; then
    up_job_name=checkout-dev
elif [[ "$build_type" == "gcc" ]]; then
    up_job_name=checkout-gcc
elif [[ "$build_type" == "svn" ]]; then
    up_job_name=checkout-dev
elif [[ "$build_type" == "bio" ]]; then
    up_job_name=checkout-biovia
elif [[ "$build_type" == "stable" ]]; then
    up_job_name=checkout-stable
elif [[ "$build_type" == "free" ]]; then
    up_job_name=checkout-free
fi

echo "upstream job name ${up_job_name}"

upstream_dir=$jenkins_jobs_dir/$up_job_name

charmm_build_vars=$*

echo "charmm build vars ${charmm_build_vars}"

echo "begin loading modules..."
if [[ "$1" == *intel* ]]; then
  echo "an intel build"
  source scripts/load_modules.bash em64t
elif [[ "$1" == "--with-pgi" ]]; then
  echo "a pgi build"
  source scripts/load_modules.bash pgi
elif [[ "$build_type" == "gcc" ]]; then
  echo "a gcc 10 build"
  source scripts/load_modules.bash gcc
else
  echo "a gcc build"
  source scripts/load_modules.bash cmake
fi
echo "... finished loading modules"

if [[ -d bld ]]; then
  echo "removing an old build dir"
  rm -rf bld;
fi

if [[ -d inst ]]; then
  echo "removing an old charmm install"
  rm -rf inst;
fi

echo "making a new build dir"
mkdir bld

echo "switching to the new build dir"
pushd bld || exit

echo "start configure script..."
if [[ "$build_type" == "gcc" ]]; then
  "$upstream_dir"/configure -p ../inst $charmm_build_vars --with-ninja \
        --with-gcc
elif [[ "$build_type" == *cmake* ]]; then
    "$upstream_dir"/configure -p ../inst $charmm_build_vars --with-ninja \
                   -D CUDA_HOST_COMPILER=/usr/bin/g++
else
  "$upstream_dir"/configure -p ../inst $charmm_build_vars --with-ninja
fi
echo "... configure script finished"

echo "begin compile using ninja..."
ninja install
echo "... finished with ninja"
popd || exit
echo "exited build directory"

if [[ -d bld ]]; then
  echo "removing the build dir"
  rm -rf bld;
fi

if [[ -d scripts ]]; then
  rm -rf scripts
fi
