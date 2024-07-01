# echo "switch to scl python 3.6"
# source /opt/rh/rh-python36/enable

# echo "set up environment modules"
# source /etc/profile.d/modules.sh

# echo "load common set of modules"
# module load cuda/system
# module load cmake
# module load ninja/1.8.2

# export FFTW_HOME=/usr

echo "handle environment for"
echo "  build type |$1|"

if [[ "$1" == "em64t" ]]; then
    echo "preparing for Intel build"
    source /opt/intel/oneapi/setvars.sh
    export CC=$(which icx)
    export CXX=$(which icx)
    export FC=$(which ifx)
#    module load intel/2021.4
#    module load openmm/7.4
elif [[ "$1" == "cmake" ]]; then
    echo "preparing for GCC build"
    conda activate dev
#    source /opt/rh/devtoolset-8/enable
#    module load openmm/7.5
# elif [[ "$1" == "gcc" ]]; then
#     echo "loading modules for GCC 10 build"
#     module load gcc/10
#     module load mpi/4-gcc-10
#     module load openmm/7.5
# elif [[ "$1" == "pgi" ]]; then
#     echo "loading modules for pgi build"
#     module load pgi/19.10
else
    # echo "loading modules for unknown build"
    # module load openmm/7.5
    # module load mpi/1.10.5
    echo "unknown build; doing nothing"
fi
