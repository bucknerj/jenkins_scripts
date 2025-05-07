def charmmConfigs = [
    'lite': '--without-python --with-intel --lite',
    'domdec_gpu': '--without-python -u --with-intel -D CMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc -D CMAKE_CUDA_HOST_COMPILER=/usr/bin/g++',
    'blade': '-u --with-blade --with-intel -D CMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc -D CMAKE_CUDA_HOST_COMPILER=/usr/bin/g++',
    'sccdftb': '--without-python --with-sccdftb --with-intel',
    'repdstr': '--without-python --with-repdstr --with-intel',
    'stringm': '--without-python --with-stringm --with-intel',
    'misc': '--without-python -a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS --with-intel',
    'misc2': '--without-python --without-domdec --with-g09 -a DISTENE,MTS --with-intel',
    'tamd': '--without-python --without-mpi -a TAMD --with-intel',
    'mndo97': '--without-python --with-mndo97 --with-intel',
    'gamus': '--without-python --with-gamus --with-intel',
    'squantm': '--without-python --with-squantm --with-intel',
    'ljpme': '--without-python --with-ljpme --with-intel',
    'resize': '--without-python -a RESIZE --with-intel'
]

def charmmTests = [
    'domdec_gpu': 'M 2 X 2 cmake',
    'blade': 'cmake',
    'sccdftb': 'cmake',
    'repdstr': 'M 2 X 2 cmake',
    'stringm': 'M 8 X 2 cmake',
    'misc': 'M 2 X 2 cmake',
    'misc2': 'M 2 X 2 cmake',
    'tamd': 'cmake',
    'mndo97': 'cmake',
    'gamus': 'cmake',
    'squantm': 'cmake',
    'ljpme': 'M 2 X 2 cmake',
    'resize': 'M 2 X 2 cmake'
]

pipeline {
    agent any
    stages {
	stage('Checkout') {
	    steps {
		git branch: 'master', url: 'gitlab:/bucknerj/dev-release'
	    }
	}
	stage("Configure") {
	    steps {
		script {
                    def parallelJobs = [:]
		    charmmConfigs.each { name, configArgs ->
			parallelJobs["Configure ${name}"] = {
			    stage("Configure ${name}") {
    			        echo "Configuring ${name}..."
    			        sh """
                                  module use /home/bucknerj/modulefiles
                                  module load compiler/latest mkl/latest mpi/latest
                                  if [[ ! -d install-${name} ]]; then
                                    tool/NewCharmmTree install-${name}
                                  fi
                                  pushd install-${name}
                                  rm -rf build/cmake
                                  ./configure --with-ninja ${configArgs}
                                  popd
                                """
    				echo "...finished configuring ${name}"
			    }
			}
		    }
		    parallel parallelJobs
		}
	    }
	}
	stage("Build") {
	    steps {
		script {
                    def parallelJobs = [:]
		    charmmConfigs.each { name, configArgs ->
			parallelJobs["Build ${name}"] = {
			    stage("Build ${name}") {
				echo "Building ${name}..."
			        sh """
                                  module use /home/bucknerj/modulefiles
                                  module load compiler/latest mkl/latest mpi/latest
                                  pushd install-${name}
                                  ninja -j 2 -C build/cmake install
                                  popd
                                """
				echo "...finished building ${name}"
			    }
			}
		    }
		    parallel parallelJobs
		}
	    }
	}
	stage("Test") {
	    steps {
		script {
                    def parallelJobs = [:]
		    charmmTests.each { name, testArgs ->
			parallelJobs["Test ${name}"] = {
			    stage("Test ${name}") {
				echo "Testing ${name}..."
				sh """
                                  module use /home/bucknerj/modulefiles
                                  module load compiler/latest mkl/latest mpi/latest
                                  pushd install-${name}/test
                                  if [[ -d output ]]; then
                                    rm -rf old
                                    mkdir old
                                    cp -r output* old/
                                    rm -rf output*
                                  fi
                                  if [[ -d old ]]; then
                                    if [[ -f test.log ]]; then
                                      cp test.log old/
                                      rm test.log
                                    fi
                                    if [[ -f compare.log ]]; then
                                      cp compare.log old/
                                      rm compare.log
                                    fi
                                    if [[ -f diff.log ]]; then
                                      cp diff.log old/
                                      rm diff.log
                                    fi
                                    if [[ -f test_results.xml ]]; then
                                      cp test_results.xml old/
                                      rm test_results.xml
                                    fi
                                  fi
                                  ./test.com ${testArgs} output old/output &> test.log
                                  popd
                                """
                		echo "...finished testing ${name}"
        		    }
        		}
		    }
		    parallel parallelJobs
		}
	    }
	}
	stage("Compare") {
	    steps {
		script {
                    def parallelJobs = [:]
		    charmmTests.each { name, testArgs ->
			parallelJobs["Compare ${name}"] = {
			    stage("Compare ${name}") {
				echo "Comparing ${name}..."
        			sh """
                                  module use /home/bucknerj/modulefiles
                                  module load compiler/latest mkl/latest mpi/latest
                                  pushd install-${name}/test
                                  export CMPDIR=old/output
                                  CMPDIR=old/output ../tool/Compare out put &> compare.log
                                  CMPDIR=old/output ../tool/Compare out put v &> diff.log
                                  popd
                                """
                		echo "...finished comparing ${name}"
                	    }
                	}
		    }
		    parallel parallelJobs
		}
	    }
	}
	stage("Grade") {
	    steps {
		script {
		    def parallelJobs = [:]
		    charmmTests.each { name, testArgs ->
			parallelJobs["Grade ${name}"] = {
			    stage("Grade ${name}") {
        			echo "Grading ${name}..."
        			sh """
                                  eval "\$(/home/bucknerj/.local/bin/micromamba shell hook --shell zsh)"
                                  micromamba activate workshop
                                  pushd install-${name}/test
                                  # call python script here
                                  python ../../config/new-test-grader.py &> ${name}.xml
                                  popd
                                """
                		junit "install-${name}/test/${name}.xml"
                		echo "...finished grading ${name}"
                	    }
        		}
		    }
		    parallel parallelJobs
		}
	    }
	}
    }
}
