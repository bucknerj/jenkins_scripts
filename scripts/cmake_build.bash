#!/bin/bash

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
    ../charmm/configure -p ../inst $charmm_build_vars
elif [[ "$1" == "--with-pgi" ]]; then
    ../charmm/configure -p ../inst $charmm_build_vars
else
    ../charmm/configure -p ../inst $charmm_build_vars
fi
make -j4 install
popd
