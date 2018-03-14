. /opt/rh/rh-python35/enable
. /etc/profile.d/modules.sh

module load cuda/9.1
module load openmm/7.2

if [[ "$1" == "em64t" ]]; then
    module load intel/16.x
    module load mpi/2.0-intel-16
elif [[ "$1" == "cmake" ]]; then 
    module load mpi/3.0-gcc-7.2
    . /opt/rh/devtoolset-7/enable
else
    module load mpi/1.10.5
fi

export FFTW_HOME=/usr
