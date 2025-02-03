# echo "switch to scl python 3.6"
# source /opt/rh/rh-python36/enable

# echo "set up environment modules"
# source /etc/profile.d/modules.sh

# echo "load common set of modules"
# module load cuda/system
# module load cmake
# module load ninja/1.8.2

# export FFTW_HOME=/usr

# >>> mamba initialize >>>
# !! Contents within this block are managed by 'micromamba shell init' !!
export MAMBA_EXE='/home/bucknerj/.local/bin/micromamba';
export MAMBA_ROOT_PREFIX='/home/bucknerj/micromamba';
__mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"  # Fallback on help from micromamba activate
fi
unset __mamba_setup
# <<< mamba initialize <<<

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
