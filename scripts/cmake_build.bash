#!/bin/bash

charmm_build_vars=$*

. scripts/load_modules.bash

if [[ -d bld ]]; then
	rm -rf bld;
fi

if [[ -d inst ]]; then
	rm -rf inst;
fi

mkdir bld

pushd bld
../charmm/configure -p ../inst $charmm_build_vars
make -j4 install
popd
