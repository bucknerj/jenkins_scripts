#!/bin/bash
echo 'BEGIN BUILD SCRIPT'

jenkins_jobs_dir=$(dirname "$WORKSPACE")
this_job_name=$(basename "$WORKSPACE")
build_type=''
up_job_name=''
if [[ $this_job_name == *dev* ]]; then
    build_type=dev
    up_job_name=checkout-dev
elif [[ $this_job_name == *stable* ]]; then
    build_type=stable
    up_job_name=checkout-stable
else
    echo "ERROR: UNKOWN BUILD TYPE"
    exit 1
fi

upstream_dir=$jenkins_jobs_dir/$up_job_name
charmm_build_vars=$*

echo "DETECTED: build type ${build_type}"
echo "DETECTED: upstream job name ${up_job_name}"
echo "DETECTED: charmm build vars ${charmm_build_vars}"

echo "begin configuring environment..."
if [[ "$this_job_name" == *intel* ]]; then
  echo "an intel build"
  source scripts/load_modules.bash intel
else
  echo "a gcc build"
  source scripts/load_modules.bash gcc
fi
echo "...finished configuring environment"

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
echo 'END BUILD SCRIPT'
