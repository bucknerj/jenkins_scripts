job('checkout-stable') {
  displayName('checkout stable')
  description('use git to checkout stable from our gitlab server')
  multiscm {
    git {
      branch('stable-release')
      remote {
        name('origin')
        url('ssh://git@charmm-dev.org:65492/bucknerj/dev-release')
        credentials('git')
      }
    }
  }
  triggers {
    scm('@daily')
  }
  publishers {
    mailer('bucknerj@umich.edu', true, true)
  }
} // end checkout job

def cmakeBuilds =
  [ [ name: 'lite', build: '--lite -g', test: 'cmake' ]
  , [ name: 'blade', build: --with-blade --with-gcc', test: 'cmake']
  , [ name: 'openmm'
    , build: '--with-gcc --without-mkl --with-fftdock'
    , test: 'cmake'
    ]
  , [ name: 'domdec_gpu'
    , build: '-u --with-gcc --without-mkl --with-fftdock'
    , test: 'M 2 X 2 cmake'
    ]
  , [ name:'intel', build:'--with-intel', test:'M 2 X 2 cmake' ]
  , [ name:'pgi', build:'--with-pgi --without-openmm --without-mpi', test:'cmake' ]
  , [ name:'sccdftb' , build:'--with-sccdftb' , test:'cmake' ]
  , [ name:'repdstr' , build:'--with-repdstr' , test:'M 2 X 2 cmake' ]
  , [ name: 'gamus', build: '--with-gamus' , test: 'cmake' ]
  , [ name: 'mndo97'
    , build: '--with-mndo97 --with-gcc --without-mkl'
    , test: 'cmake'
    ]
  , [ name: 'squantm'
    , build: '-a SQUANTM -r QUANTUM,QCHEM,MNDO97 --with-gcc --without-mkl'
    , test: 'cmake'
    ]
  , [ name:'misc'
    , build:'-a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS'
    , test:'M 2 X 2 cmake'
    ]
  , [ name:'misc2'
    , build:'--without-domdec --with-g09 -a DISTENE,MTS'
    , test:'M 2 X 2 cmake'
    ]
  , [ name:'ljpme', build:'--with-ljpme', test:'M 2 X 2 cmake' ]
  ];

// umich stable builds
cmakeBuilds.each {
  def current = it
// umich CMake build and test
job("build-stable-cmake-${current.name}") {
  displayName("build stable cmake ${current.name}")
  description("${current.name}\nconfigure ${current.build}\ntest ${current.test}")
  multiscm {
    git {
      branch('master')
      remote {
        name('origin')
        url('/opt/git/jenkins.git')
      }
      extensions {
        relativeTargetDirectory('config')
      }
    }
  }
  triggers {
    upstream('checkout-stable')
  }
  steps {
    shell("/bin/bash -e config/scripts/cmake_build.bash ${current.build}")
  }
  publishers {
    mailer('bucknerj@umich.edu', true, true)
  }
} // end stable CMake build job

// begin stable CMake test job
job("test-stable-cmake-${current.name}") {
  displayName("test stable cmake ${current.name}")
  description("${current.name}\nconfigure ${current.build}\ntest ${current.test}")
  multiscm {
    git {
      branch('master')
      remote {
        name('origin')
        url('/opt/git/jenkins.git')
      }
      extensions {
        relativeTargetDirectory('config')
      }
    }
  }
  triggers {
    upstream("build-stable-cmake-${current.name}")
  }
  steps {
    shell("/bin/bash config/scripts/test.bash ${current.test}")
  }
  publishers {
    archiveXUnit {
      jUnit {
          pattern('xml/c*test.xml')
      }
      skippedThresholds {
        failure(80)
        failureNew(80)
        unstable(50)
        unstableNew(50)
      }
      thresholdMode(ThresholdMode.PERCENT)
    }
  }
} // end stable CMake test job
} // end stable CMake jobs
