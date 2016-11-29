#!/bin/bash

charmm_build_vars=$*

. config/scripts/load_modules.bash $1

if [[ -d inst ]]; then
	rm -rf inst;
fi
charmm/tool/NewCharmmTree inst

export MAKE_COMMAND='make -j4 '
pushd inst
./install.com $charmm_build_vars keepf nolog
popd
