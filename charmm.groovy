job('checkout-charmm') {
  displayName('checkout charmm')
  description('use git to checkout charmm from our gitlab server')
  multiscm {
    git {
      branch('master')
      remote {
        name('origin')
        url('ssh://git@charmm-dev.org:65492/bucknerj/charmm')
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
  , [name: 'openmm', build: '--with-fftdock', test: 'cmake']
  , [name: 'domdec_gpu', build: '-u --with-gcc --with-fftdock', test: 'M 2 X 2 cmake']
  , [name: 'blade', build: '-u --with-blade --with-gcc', test: 'cmake']
  , [name:'intel', build:'--with-intel', test:'M 2 X 2 cmake']
  , [name:'sccdftb' , build:'--with-sccdftb' , test:'cmake']
  , [name:'repdstr' , build:'--with-repdstr' , test:'M 2 X 2 cmake']
  , [name:'stringm', build:'--with-stringm', test:'M 8 X 2 cmake']
  , [ name:'misc'
    , build:'-a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS'
    , test:'M 2 X 2 cmake'
    ]
  , [ name:'misc2'
    , build:'--without-domdec --with-g09 -a DISTENE,MTS'
    , test:'M 2 X 2 cmake'
    ]
  , [name:'tamd', build:'--without-mpi -a TAMD', test:'cmake']
  , [name: 'mndo97', build: '--with-mndo97', test: 'cmake']
  , [name: 'gamus', build: '--with-gamus' , test: 'cmake']
  , [name: 'squantm', build: '--with-squantm', test: 'cmake']
  , [ name:'pgi', build:'--with-pgi --without-openmm --without-mpi', test:'cmake' ]
  , [ name:'ljpme', build:'--with-ljpme', test:'M 2 X 2 cmake' ]
  ];

// umich git builds
cmakeBuilds.each {
  def current = it
// umich CMake build and test
job("build-git-cmake-${current.name}") {
  displayName("build git cmake ${current.name}")
  description("${current.description}\nconfigure ${current.build}")
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
    upstream('checkout-charmm')
  }
  steps {
    shell("/bin/bash -e config/scripts/cmake_build.bash ${current.build}")
  }
  publishers {
    mailer('bucknerj@umich.edu', true, true)
  }
} // end git CMake build job

// begin git CMake test job
job("test-git-cmake-${current.name}") {
  displayName("test git cmake ${current.name}")
  description("run the testcases for cmake\n${current.description}\nconfigure ${current.build}\ntest ${current.test}")
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
    upstream("build-git-cmake-${current.name}")
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
} // end git CMake test job
} // end git CMake jobs
