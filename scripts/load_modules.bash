echo "switch to scl python 3.6"
source scl_source enable rh-python36

echo "set up environment modules"
source /etc/profile.d/modules.sh

echo "load common set of modules"
module load cuda/system
module load cmake
module load ninja

export FFTW_HOME=/usr

echo "build type |$1|"

if [[ "$1" == "em64t" ]]; then
    echo "loading modules for Intel 18 build"
    module load openmm/7.4
    module load intel/18.x
    module load mpi/3.0-intel-18
elif [[ "$1" == "cmake" ]]; then
    echo "loading modules for GCC 9 build"
    source scl_source enable devtoolset-9
    module load openmm/7.4
    module load mpi/4-scl-9
elif [[ "$1" == "pgi" ]]; then
    echo "loading modules for pgi build"
    source scl_source enable devtoolset-9
    module load openmm/7.2
    module load pgi/18.4
else
    echo "loading modules for unknown build"
    module load openmm/7.4
    module load mpi/1.10.5
fi
