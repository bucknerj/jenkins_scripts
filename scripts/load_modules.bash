export MODULESHOME=/usr/local/Modules/3.2.10
source $MODULESHOME/init/sh

module load OpenMM/6.3.0
module load FFTW/3.3.5

if [[ "$1" == "em64t" ]]; then
  module load Intel/2015
  module load openmpi/2.0-intel-15
else
  module load openmpi/2.0-gcc-system
fi

# now relying on system to provide gfortran, fftw, and openmpi-gcc
