#!/bin/bash

# Initialize micromamba
export MAMBA_EXE='/home/bucknerj/.local/bin/micromamba'
export MAMBA_ROOT_PREFIX='/home/bucknerj/micromamba'
__mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"
fi
unset __mamba_setup

echo "configure environment for build type |$1|"

if [[ "$1" == "intel" ]]; then
    echo "preparing for Intel build"
    source /opt/intel/oneapi/setvars.sh
    export OMP_NUM_THREADS=2
    export CC=$(which icx)
    export CXX=$(which icpx)
    export FC=$(which ifx)
elif [[ "$1" == "gcc" ]]; then
    echo "preparing for GCC build"
    micromamba activate workshop
    export FFTW_HOME=$CONDA_PREFIX
else
    echo "ERROR: unknown build; doing nothing"
    exit 1
fi
