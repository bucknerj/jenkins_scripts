pipeline {
    agent any
    stages {
	stage('Checkout') {
	    steps {
		git branch: 'stable-release', url: 'gitlab:/bucknerj/dev-release'
	    }
	}
	stage('Configure') {
	    steps {
		echo 'Configuring...'
		sh '''
                  eval "$(/home/bucknerj/.local/bin/micromamba shell hook --shell zsh)"
                  micromamba activate dev
                  rm -rf build/cmake
                  ./configure -g --with-ninja
                '''
		echo '...finished configuring'
	    }
	}
	stage('Build') {
	    steps {
		echo 'Building...'
		sh '''
                  eval "$(/home/bucknerj/.local/bin/micromamba shell hook --shell zsh)"
                  micromamba activate dev
                  ninja -C build/cmake install
                '''
		echo '...finished building'
	    }
	}
	stage('Test') {
	    steps {
		echo 'Testing...'
		sh '''
                  eval "$(/home/bucknerj/.local/bin/micromamba shell hook --shell zsh)"
                  micromamba activate dev
                  pushd test
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
                  ./test.com cmake output old/output &> test.log
                  popd
                '''
		echo '...finished testing'
	    }
	}
	stage('Compare') {
	    steps {
		echo 'Comparing...'
		sh '''
                  eval "$(/home/bucknerj/.local/bin/micromamba shell hook --shell zsh)"
                  micromamba activate dev
                  pushd test
                  export CMPDIR=old/output
                  CMPDIR=old/output ../tool/Compare out put &> compare.log
                  CMPDIR=old/output ../tool/Compare out put v &> diff.log
                  popd
                '''
		echo '...finished comparing'
	    }
	}
	stage('Grade') {
	    steps {
		echo 'Grading...'
		sh '''
                  eval "$(/home/bucknerj/.local/bin/micromamba shell hook --shell zsh)"
                  micromamba activate dev
                  pushd test
                  # call python script here
                  python ../config/new-test-grader.py &> test_results.xml
                  popd
                '''
		junit 'test/test_results.xml'
		echo '...finished grading'
	    }
	}
    }
}
