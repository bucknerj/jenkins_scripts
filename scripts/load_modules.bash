. /opt/rh/rh-python35/enable
. /etc/profile.d/modules.sh

module load cuda/9.1
module load openmm/7.2

if [[ "$1" == "em64t" ]]; then
    module load intel/18.x
    module load mpi/3.0-intel-18
    export CUDA_HOST_COMPILER=/opt/intel/bin/icpc
elif [[ "$1" == "cmake" ]]; then
    . /opt/rh/devtoolset-7/enable
    module load mpi/3.0-gcc-7.2
    export CUDA_HOST_COMPILER=/usr/bin/g++
else
    module load mpi/1.10.5
fi

export FFTW_HOME=/usr
