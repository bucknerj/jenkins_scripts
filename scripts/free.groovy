job('checkout-free') {
  displayName('checkout free')
  description('use git to checkout free from our gitlab server')
  multiscm {
    git {
      branch('free')
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
  , [ name:'repdstr'
    , build:'gnu M +REPDSTR +ASYNC_PME +GENCOMM +MSCALE'
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

// umich free builds
builds.each {
  def current = it
  job("build-free-${current.name}") {
    displayName("build free ${current.name}")
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
      upstream('checkout-free')
    }
    steps {
      shell("/bin/bash -e config/scripts/build.bash ${current.build}")
    }
    publishers {
      mailer('bucknerj@umich.edu', true, true)
    }
  } // end free build job

  if (current.test) {
    job("test-free-${current.name}") {
      displayName("test free ${current.name}")
      description("run the testcases for the free ${current.name} build")
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
        upstream("build-free-${current.name}")
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
    } // end free test job
  } // end if current.test
} // end build.each

def cmakeBuilds =
  [ [ name: 'lite', build: '--lite -g', test: 'cmake' ]
  , [ name: 'openmm'
    , build: '--with-gcc'
    , test: 'cmake'
    ]
  , [ name:'intel', build:'--with-intel', test:'M 2 X 2 cmake' ]
  , [ name:'pgi', build:'--with-pgi --without-openmm --without-mpi', test:'cmake' ]
  , [ name:'sccdftb' , build:'--with-sccdftb' , test:'cmake' ]
  , [ name:'repdstr' , build:'--with-repdstr' , test:'M 2 X 2 cmake' ]
  , [ name: 'gamus', build: '--with-gamus' , test: 'cmake' ]
  , [ name: 'mndo97' , build: '--with-mndo97' , test: 'cmake' ]
  , [ name: 'squantm' , build: '--with-squantm' , test: 'cmake' ]
  , [ name:'misc'
    , build:'-a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS'
    , test:'M 2 X 2 cmake'
    ]
  , [ name:'misc2' , build:'--with-g09 -a DISTENE,MTS' , test:'M 2 X 2 cmake' ]
  , [ name:'ljpme', build:'--with-ljpme', test:'M 2 X 2 cmake' ]
  ];

// umich free builds
cmakeBuilds.each {
  def current = it
// umich CMake build and test
job("build-free-cmake-${current.name}") {
  displayName("build free cmake ${current.name}")
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
    upstream('checkout-free')
  }
  steps {
    shell("/bin/bash -e config/scripts/cmake_build.bash ${current.build}")
  }
  publishers {
    mailer('bucknerj@umich.edu', true, true)
  }
} // end free CMake build job

// begin free CMake test job
job("test-free-cmake-${current.name}") {
  displayName("test free cmake ${current.name}")
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
    upstream("build-free-cmake-${current.name}")
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
} // end free CMake test job
} // end free CMake jobs
