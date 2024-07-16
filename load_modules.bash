# echo "switch to scl python 3.6"
# source /opt/rh/rh-python36/enable

# echo "set up environment modules"
# source /etc/profile.d/modules.sh

# echo "load common set of modules"
# module load cuda/system
# module load cmake
# module load ninja/1.8.2

# export FFTW_HOME=/usr

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/bucknerj/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/bucknerj/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/home/bucknerj/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/home/bucknerj/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

echo "configure environment for build type |$1|"

if [[ "$1" == "intel" ]]; then
    echo "preparing for Intel build"
    source /opt/intel/oneapi/setvars.sh
    export CC=$(which icx)
    export CXX=$(which icx)
    export FC=$(which ifx)
elif [[ "$1" == "gcc" ]]; then
    echo "preparing for GCC build"
    conda activate dev
else
    echo "ERROR: unknown build; doing nothing"
    exit 1
fi
