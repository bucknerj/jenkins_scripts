# export MODULESHOME=/usr/local/Modules/3.2.10
# source $MODULESHOME/init/sh

# module load OpenMM/6.3.0
# module load FFTW/3.3.5

# now relying on system to provide gfortran, fftw, and openmpi-gcc
. /opt/rh/rh-python35/enable
. /etc/profile.d/modules.sh
if [[ "$1" == "em64t" ]]; then
    module load intel/16.x
    module load mpi/2.0-intel-16
elif [[ "$1" == "cmake" ]]; then 
    module load mpi/3.0-gcc-7.2
    . /opt/rh/devtoolset-7/enable
else
    module load mpi/1.10.5
fi

export PATH=/usr/local/cuda/bin:$PATH
export FFTW_HOME=/usr
