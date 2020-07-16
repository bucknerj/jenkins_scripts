job('checkout-dev') {
  displayName('checkout dev')
  description('use git to checkout dev from our gitlab server')
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
  , [name:'intel', build:'--with-intel', test:'M 2 X 2 cmake']
  , [name:'sccdftb' , build:'--with-sccdftb' , test:'cmake']
  , [name:'repdstr' , build:'--with-repdstr' , test:'M 2 X 2 cmake']
  , [name:'stringm', build:'--with-stringm', test:'M 8 X 2 cmake']
  , [ name:'misc'
    , build:'-a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS'
    , test:'M 2 X 2 cmake'
    ]
  , [name:'misc2' , build:'--with-g09 -a DISTENE,MTS' , test:'M 2 X 2 cmake']
  , [name:'tamd', build:'-a TAMD', test:'cmake']
  , [name: 'mndo97', build: '--with-mndo97', test: 'cmake']
  , [name: 'gamus', build: '--with-gamus' , test: 'cmake']
  , [name: 'squantm', build: '--with-squantm', test: 'cmake']
  ];

// umich dev builds
cmakeBuilds.each {
  def current = it
// umich CMake build and test
job("build-dev-${current.name}") {
  displayName("build dev cmake ${current.name}")
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
    upstream('checkout-dev')
  }
  steps {
    shell("/bin/bash -e config/scripts/cmake_build.bash ${current.build}")
  }
  publishers {
    mailer('bucknerj@umich.edu', true, true)
  }
} // end dev CMake build job

// begin dev CMake test job
job("test-dev-${current.name}") {
  displayName("test dev ${current.name}")
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
    upstream("build-dev-${current.name}")
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
} // end dev CMake test job
} // end dev CMake jobs
