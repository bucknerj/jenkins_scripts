. /opt/rh/rh-python35/enable
. /etc/profile.d/modules.sh

module load cuda/system

if [[ "$1" == "em64t" ]]; then
    module load openmm/7.1
    module load intel/18.x
    module load mpi/3.0-intel-18
elif [[ "$1" == "cmake" ]]; then 
    module load openmm/7.2
    . /opt/rh/devtoolset-7/enable
    module load mpi/3.1-gcc-7.3
else
    module load openmm/7.1
    module load mpi/1.10.5
fi

export CUDA_HOST_COMPILER=/usr/bin/g++
export FFTW_HOME=/usr
