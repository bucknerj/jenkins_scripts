def configs = [
    [name:'lite', build:'gnu lite', test:''],

    [name:'repdstr',
     build:'--with-gcc --repdstr',
     test:'M 2 X 2 cmake'],

    [name:'misc',
     build:'--with-gcc -a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS',
     test:'M 2 X 2 cmake'],
    
    [name:'stringm',
     build:'--with-gcc --stringm',
     test:'M 8 X 2 cmake'],
    
    [ name:'tamd', build:'--with-gcc --without-mpi -a TAMD', test:'cmake' ],
    
    [name: 'openmm',
     description: 'openmm and sccdftb',
     build: '-s --with-gcc --without-mkl',
     test: 'cmake'],

    [name: 'domdec_gpu',
     description: 'domdec_gpu and openmm',
     build: '-u --with-gcc --without-mkl',
     test: 'M 2 X 2 cmake'],

    [name:'intel', build:'--with-intel', test:'M 2 X 2 cmake'],

    [name:'pgi', build:'--with-pgi -u -D CUDA_HOST_COMPILER=/home/apps/pgi/2018/linux86-64/2018/bin/pgc++', test:'M 2 X 2 cmake'],

    [name: 'mndo97',
     description: 'MNDO97',
     build: '-a MNDO97 -r QUANTUM,QCHEM --with-gcc --without-mkl',
     test: 'cmake'],

    [name: 'squantm',
     description: 'SQUANTM',
     build: '-a SQUANTM -r QUANTUM,QCHEM,MNDO97 --with-gcc --without-mkl',
     test: 'cmake']];

configs.each {
    def current = it
    
    job("build-biovia-${current.name}") {
        displayName("build biovia ${current.name}")
        description("configure ${current.build}")
        multiscm {
            git {
                branch('master')
                remote {
                    name('origin')
                    url('ssh://git@charmm-dev.org:65492/bucknerj/biovia')
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
            shell("/bin/bash -e config/scripts/cmake_build.bash ${current.build}")
        }
        publishers {
            mailer('bucknerj@umich.edu', true, true)
        }
    } // end build job

    if (current.test) {
        job("test-biovia-${current.name}") {
            displayName("test biovia ${current.name}")
            description("configure ${current.build}\ntest ${current.test}")
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
                upstream("build biovia ${current.name}")
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
        } // end test job
    }
} // end configs loop
