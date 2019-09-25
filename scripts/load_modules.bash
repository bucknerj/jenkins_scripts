. /opt/rh/rh-python35/enable
. /etc/profile.d/modules.sh

module load cuda/system

export FFTW_HOME=/usr

if [[ "$1" == "em64t" ]]; then
    module load openmm/7.4
    module load intel/18.x
    module load mpi/3.0-intel-18
elif [[ "$1" == "cmake" ]]; then 
    module load openmm/7.4
    . /opt/rh/devtoolset-8/enable
    module load mpi/4.0-scl-8.3
elif [[ "$1" == "pgi" ]]; then 
    . /opt/rh/devtoolset-7/enable
    module load openmm/7.2
    module load pgi/18.4
else
    module load openmm/7.4
    module load mpi/1.10.5
fi
