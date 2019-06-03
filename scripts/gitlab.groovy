job('build-gitlab-example') {
    displayName('build gitlab example')
    description('compile gitlab example using cmake')
    multiscm {
        git {
            branch('master')
            remote {
                name('origin')
                url('ssh://git@charmm-dev.org:65492/bucknerj/dev-release')
                credentials('git')
            }
            extensions {
                relativeTargetDirectory('charmm')
            }
        }
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
        scm('@daily')
    }
    steps {
        shell('/bin/bash -e config/scripts/cmake_build.bash -u --with-gcc --without-mkl')
    }
    publishers {
        mailer('bucknerj@umich.edu', true, true)
    }
} // end job build-gitlab-example

job('test-gitlab-example') {
    displayName('test gitlab example')
    description('run the testcases for gitlab example')
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
        upstream('build-gitlab-example')
    }
    steps {
        shell('/bin/bash config/scripts/test.bash M 2 X 16 cmake')
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
} // end job test-gitlab-example
