. /opt/rh/rh-python35/enable
. /etc/profile.d/modules.sh

module load cuda/system
module load cmake
module load ninja

export FFTW_HOME=/usr

echo "build type |$1|"

if [[ "$1" == "em64t" ]]; then
    echo "loading modules for intel build"
    module load openmm/7.4
    module load intel/18.x
    module load mpi/3.0-intel-18
elif [[ "$1" == "cmake" ]]; then
    echo "loading modules for gnu build"
    module load openmm/7.4
    module load mpi/4.0-scl-8.3
    . /opt/rh/devtoolset-8/enable
elif [[ "$1" == "pgi" ]]; then
    echo "loading modules for pgi build"
    module load openmm/7.2
    module load pgi/18.4
    . /opt/rh/devtoolset-7/enable
else
    echo "loading modules for unknown build"
    module load openmm/7.4
    module load mpi/1.10.5
fi
