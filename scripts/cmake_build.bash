#!/bin/bash

charmm_build_vars=$*

if [[ "$1" == "--with-intel" ]]; then
  . config/scripts/load_modules.bash em64t
else
  . config/scripts/load_modules.bash
fi

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
