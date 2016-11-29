def builds =
  [ [name:'lite', build:'gnu lite', test:'']
  , [name:'intel', build:'em64t M openmm mkl', test:'M 4 X 16 em64t']
  , [name:'gpu', build:'gnu M openmm domdec_gpu fftw', test:'M 4 X 16 gnu']
  , [ name:'repdstr'
    , build:'gnu M +REPDSTR +ASYNC_PME +GENCOMM +MSCALE +CMPI'
    , test:'M 4 X 16 gnu'
    ]
  ];

// umich git builds
builds.each {
  def current = it
  job("git-${current.name}.build") {
    displayName("build git ${current.name}")
    description("install.com ${current.build} debug keepf nolog")
    authorization {
      permission('hudson.model.Item.Discover', 'anonymous')
      permission('hudson.model.Item.Read', 'anonymous')
    }
    multiscm {
      git {
        branch('master')
        remote {
          name('origin')
          url('brooks:/export/git/charmm.git')
        }
        extensions {
          relativeTargetDirectory('charmm')
        }
      }
      git {
        branch('master')
        remote {
          name('origin')
          url('/export/people/jenkins/scripts.git')
        }
        extensions {
          relativeTargetDirectory('scripts')
        }
      }
    }
    triggers {
      scm('@daily')
    }
    steps {
      shell("/bin/bash -e scripts/build.bash ${current.build}")
    }
    publishers {
      mailer('bucknerj@umich.edu', true, true)
    }
  } // end git build job

  if (current.test) {
    job("git-${current.name}.test") {
      displayName("test git ${current.name}")
      description("run the testcases for the git ${current.name} build")
      authorization {
        permission('hudson.model.Item.Discover', 'anonymous')
        permission('hudson.model.Item.Read', 'anonymous')
      }
      multiscm {
        git {
          branch('master')
          remote {
            name('origin')
            url('/export/people/jenkins/scripts.git')
          }
          extensions {
            relativeTargetDirectory('scripts')
          }
        }
      }
      triggers {
        upstream("git-${current.name}.build")
      }
      steps {
        shell("/bin/bash scripts/test.bash ${current.test}")
        shell("/bin/bash scripts/email.bash > current/email.html")
      }
      publishers {
        archiveXUnit {
          jUnit {
            pattern('current/output.xml')
          }
          skippedThresholds {
            failure(80)
            failureNew(80)
            unstable(50)
            unstableNew(50)
          }
          thresholdMode(ThresholdMode.PERCENT)
        }
        extendedEmail {
          recipientList('bucknerj@umich.edu')
          defaultSubject("test git ${current.name}")
          preSendScript('''
              msg.setContent(new File("${workspace}/current/email.html").text, "text/html")
          ''')
          triggers {
            always {
              sendTo {
                recipientList()
              }
            }
            firstFailure {
              sendTo {
                recipientList()
                culprits()
              }
            }
          }
        }
      }
    } // end git test job
  } // end if current.test
} // end build.each

// hanyang svn builds
builds.each {
  def current = it
  job("svn-${current.name}.build") {
    displayName("build svn ${current.name}")
    description("install.com ${current.build} debug keepf nolog")
    authorization {
      permission('hudson.model.Item.Discover', 'anonymous')
      permission('hudson.model.Item.Read', 'anonymous')
    }
    multiscm {
      svn {
        location('svn://charmm.hanyang.ac.kr/charmm/trunk') {
          credentials('d0fd9e9e-854b-48d3-80a6-2f7df21e4c5f') 
          directory('charmm')
        }
      }
      git {
        branch('master')
        remote {
          name('origin')
          url('/export/people/jenkins/scripts.git')
        }
        extensions {
          relativeTargetDirectory('scripts')
        }
      }
    }
    triggers {
      scm('@daily')
    }
    steps {
      shell("/bin/bash -e scripts/build.bash ${current.build}")
    }
    publishers {
      mailer('bucknerj@umich.edu', true, true)
    }
  } // end svn build

  if (current.test) {
    job("svn-${current.name}.test") {
      displayName("test svn ${current.name}")
      description("run the testcases for the svn ${current.name} build")
      authorization {
        permission('hudson.model.Item.Discover', 'anonymous')
        permission('hudson.model.Item.Read', 'anonymous')
      }
      multiscm {
        git {
          branch('master')
          remote {
            name('origin')
            url('/export/people/jenkins/scripts.git')
          }
          extensions {
            relativeTargetDirectory('scripts')
          }
        }
      }
      triggers {
        upstream("svn-${current.name}.build")
      }
      steps {
        shell("/bin/bash scripts/test.bash ${current.test}")
        shell("/bin/bash scripts/email.bash > current/email.html")
      }
      publishers {
        archiveXUnit {
          jUnit {
            pattern('current/output.xml')
          }
          skippedThresholds {
            failure(80)
            failureNew(80)
            unstable(50)
            unstableNew(50)
          }
          thresholdMode(ThresholdMode.PERCENT)
        }
        extendedEmail {
          recipientList('bucknerj@umich.edu')
          defaultSubject("test svn ${current.name}")
          preSendScript('''
              msg.setContent(new File("${workspace}/current/email.html").text, "text/html")
          ''')
          triggers {
            always {
              sendTo {
                recipientList()
              }
            }
            firstFailure {
              sendTo {
                recipientList()
                culprits()
              }
            }
          }
        }
      }
    }  // end svn test
  } // end if current.test
} // end svn job configurations

def cmakeBuilds =
  [ [ name: 'openmm'
    , description: 'openmm and sccdftb'
    , build: '-s --with-gcc --without-mkl'
    , test: 'cmake'
    ]
  , [ name: 'domdec_gpu'
    , description: 'domdec_gpu and openmm'
    , build: '-u --with-gcc --without-mkl'
    , test: 'M 4 X 16 cmake'
    ]
  , [ name: 'mndo97'
    , description: 'MNDO97'
    , build: '-a MNDO97 -r QUANTUM,QCHEM --with-gcc --without-mkl'
    , test: 'cmake'
    ]
  , [ name: 'squantm'
    , description: 'SQUANTM'
    , build: '-a SQUANTM -r QUANTUM,QCHEM,MNDO97 --with-gcc --without-mkl'
    , test: 'cmake'
    ]
  ];

// umich git builds
cmakeBuilds.each {
  def current = it
// umich CMake build and test
job("git-cmake-${current.name}.build") {
  displayName("build git cmake ${current.name}")
  description("${current.description}\nconfigure ${current.build}")
  authorization {
    permission('hudson.model.Item.Discover', 'anonymous')
    permission('hudson.model.Item.Read', 'anonymous')
  }
  multiscm {
    git {
      branch('master')
      remote {
        name('origin')
        url('brooks:/export/git/charmm.git')
      }
      extensions {
        relativeTargetDirectory('charmm')
      }
    }
    git {
      branch('master')
      remote {
        name('origin')
        url('/export/people/jenkins/scripts.git')
      }
      extensions {
        relativeTargetDirectory('scripts')
      }
    }
  }
  triggers {
    scm('@daily')
  }
  steps {
    shell("/bin/bash -e scripts/cmake_build.bash ${current.build}")
  }
  publishers {
    mailer('bucknerj@umich.edu', true, true)
  }
} // end git CMake build job

// begin git CMake test job
job("git-cmake-${current.name}.test") {
  displayName("test git cmake ${current.name}")
  description("run the testcases for cmake\n${current.description}\nconfigure ${current.build}\ntest ${current.test}")
  authorization {
    permission('hudson.model.Item.Discover', 'anonymous')
    permission('hudson.model.Item.Read', 'anonymous')
  }
  multiscm {
    git {
      branch('master')
      remote {
        name('origin')
        url('/export/people/jenkins/scripts.git')
      }
      extensions {
        relativeTargetDirectory('scripts')
      }
    }
  }
  triggers {
    upstream("git-cmake-${current.name}.build")
  }
  steps {
    shell("/bin/bash scripts/test.bash ${current.test}")
    shell("/bin/bash scripts/email.bash > current/email.html")
  }
  publishers {
    archiveXUnit {
      jUnit {
        pattern('current/output.xml')
      }
      skippedThresholds {
        failure(80)
        failureNew(80)
        unstable(50)
        unstableNew(50)
      }
      thresholdMode(ThresholdMode.PERCENT)
    }
    extendedEmail {
      recipientList('bucknerj@umich.edu')
      defaultSubject("test git cmake ${current.name}")
      preSendScript('''
          msg.setContent(new File("${workspace}/current/email.html").text, "text/html")
      ''')
      triggers {
        always {
          sendTo {
            recipientList()
          }
        }
        firstFailure {
          sendTo {
            recipientList()
            culprits()
          }
        }
      }
    }
  }
} // end git CMake test job
} // end git CMake jobs
