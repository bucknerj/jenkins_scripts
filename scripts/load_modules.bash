echo "switch to scl python 3.6"
source /opt/rh/rh-python36/enable

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
    module load intel/18.x
    module load mpi/3.0-intel-18
    module load openmm/7.4
elif [[ "$1" == "cmake" ]]; then
    echo "loading modules for GCC 8 build"
    source /opt/rh/devtoolset-8/enable
    module load openmm/7.5
    module load mpi/4.0-scl-8.3
elif [[ "$1" == "gcc" ]]; then
    echo "loading modules for GCC 10 build"
    module load gcc/10
    module load mpi/4-gcc-10
    module load openmm/7.5
elif [[ "$1" == "pgi" ]]; then
    echo "loading modules for pgi build"
    module load pgi/19.10
else
    echo "loading modules for unknown build"
    module load openmm/7.5
    module load mpi/1.10.5
fi
