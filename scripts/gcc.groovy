job('checkout-gcc') {
  displayName('checkout gcc')
  description('use git to checkout the gcc 10 fix from our gitlab server')
  multiscm {
    git {
      branch('master')
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
  [ [name: 'lite', build: '--lite -g', test: 'cmake']
  , [name: 'openmm', build: '', test: 'cmake']
  , [name: 'domdec_gpu', build: '-u --with-gcc', test: 'M 2 X 2 cmake']
  , [name: 'blade', build: '-u --with-blade --with-gcc', test: 'cmake']
  , [name: 'sccdftb' , build:'--with-sccdftb' , test:'cmake']
  , [name: 'repdstr' , build:'--with-repdstr' , test:'M 2 X 2 cmake']
  , [name: 'stringm', build:'--with-stringm', test:'M 8 X 2 cmake']
  , [ name: 'misc'
    , build: '-a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS'
    , test: 'M 2 X 2 cmake'
    ]
  , [ name: 'misc2'
    , build: '--without-domdec --with-g09 -a DISTENE,MTS'
    , test: 'M 2 X 2 cmake'
    ]
  , [name: 'tamd', build:'--without-mpi -a TAMD', test:'cmake']
  , [name: 'mndo97', build: '--with-mndo97', test: 'cmake']
  , [name: 'gamus', build: '--with-gamus' , test: 'cmake']
  , [name: 'squantm', build: '--with-squantm', test: 'cmake']
  , [name: 'ljpme', build:'--with-ljpme', test:'M 2 X 2 cmake' ]
  ];

// umich gcc builds
cmakeBuilds.each {
  def current = it
// umich CMake build and test
job("build-gcc-${current.name}") {
  displayName("build gcc ${current.name}")
  description("${current.name}\n${current.build}\n${current.test}")
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
    upstream('checkout-gcc')
  }
  steps {
    shell("/bin/bash -e config/scripts/cmake_build.bash ${current.build}")
  }
  publishers {
    mailer('bucknerj@umich.edu', true, true)
  }
} // end dev CMake build job

// begin dev CMake test job
job("test-gcc-${current.name}") {
  displayName("test gcc ${current.name}")
  description("${current.name}\n${current.build}\n${current.test}")
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
    upstream("build-gcc-${current.name}")
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
} // end dev CMake test job
} // end dev CMake jobs
