job('checkout-stable') {
  displayName('checkout stable')
  description('use git to checkout stable from our gitlab server')
  multiscm {
    git {
      branch('master')
      remote {
        name('origin')
        url('ssh://git@charmm-dev.org:65492/bucknerj/stable-release')
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

def builds =
  [ [name:'lite', build:'gnu lite', test:'']
  , [name:'intel', build:'em64t M openmm mkl', test:'M 2 X 2 em64t']
  , [name:'openmm', build:'gnu openmm fftw', test:'gnu']
  , [name:'gpu', build:'gnu M domdec_gpu fftw', test:'M 2 X 2 gnu']
  , [ name:'repdstr'
    , build:'gnu M +REPDSTR +ASYNC_PME +GENCOMM +MSCALE +CMPI'
    , test:'M 2 X 2 gnu'
    ]
  , [ name:'misc'
    , build:'gnu M +ABPO +ADUMBRXNCOR +ROLLRXNCOR +CORSOL +CVELOCI +PINS +ENSEMBLE +SAMC +MCMA +GSBP +PIPF +POLAR +PNM +RISM +CONSPH +RUSH +TMD +DIMS +MSCALE +EDS'
    , test:'M 2 X 2 gnu'
    ]
  , [ name:'stringm', build:'gnu M stringm', test:'M 8 X 2 gnu' ]
  , [ name:'misc2'
    , build:'gnu M g09 +DISTENE +MTS'
    , test:'M 2 X 2 gnu'
    ]
  , [ name:'tamd', build:'gnu +TAMD', test:'gnu' ]
  ];

// umich stable builds
builds.each {
  def current = it
  job("build-stable-${current.name}") {
    displayName("build stable ${current.name}")
    description("install.com ${current.build} debug keepf nolog")
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
      shell("/bin/bash -e config/scripts/build.bash ${current.build}")
    }
    publishers {
      mailer('bucknerj@umich.edu', true, true)
    }
  } // end stable build job

  if (current.test) {
    job("test-stable-${current.name}") {
      displayName("test stable ${current.name}")
      description("run the testcases for the stable ${current.name} build")
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
        upstream("build-stable-${current.name}")
      }
      steps {
        shell("/bin/bash config/scripts/test.bash ${current.test}")
      }
      publishers {
        archiveXUnit {
          jUnit {
            pattern('new/xml/c*test.xml')
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
    } // end stable test job
  } // end if current.test
} // end build.each

def cmakeBuilds =
  [ [ name: 'lite', build: '--lite -g', test: 'cmake' ]
  , [ name: 'openmm'
    , build: '--with-gcc --without-mkl'
    , test: 'cmake'
    ]
  , [ name: 'domdec_gpu'
    , build: '-u --with-gcc --without-mkl'
    , test: 'M 2 X 2 cmake'
    ]
  , [ name:'intel', build:'--with-intel', test:'M 2 X 2 cmake' ]
  , [ name:'pgi', build:'--with-pgi', test:'cmake' ]
  , [ name:'sccdftb' , build:'--with-sccdftb' , test:'cmake' ]
  , [ name:'repdstr' , build:'--with-repdstr' , test:'M 2 X 2 cmake' ]
  , [ name: 'gamus', build: '--with-gamus' , test: 'cmake' ]
  , [ name: 'mndo97'
    , build: '-a MNDO97 -r QUANTUM,QCHEM --with-gcc --without-mkl'
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
          pattern('new/xml/c*test.xml')
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
