// Resource limits — morrison has 16 cores; reserve 4 for desktop use
def MAX_BUILD_CONCURRENT = 2   // concurrent ninja builds
def BUILD_THREADS = 6          // -j per build (2 × 6 = 12 cores)
def MAX_TEST_CONCURRENT = 3    // concurrent test runs

// GPU tests run sequentially to avoid GPU memory contention
def GPU_TESTS = ['domdec_gpu', 'blade'] as Set

def PIP_LOCK = '-D pip_lock=ON'

def charmmConfigs = [
    'lite': "--lite ${PIP_LOCK}",  // build-only, verifies compilation
    'openmm': "--with-fftdock ${PIP_LOCK}",
    'domdec_gpu': "-u --with-fftdock ${PIP_LOCK}",
    'blade': "-u --with-blade --with-fftdock ${PIP_LOCK}",
    'pycharmm': "--with-fftdock ${PIP_LOCK}",  // pyCHARMM pytest
    'sccdftb': "--with-sccdftb ${PIP_LOCK}",
    'repdstr': "--with-repdstr ${PIP_LOCK}",
    'stringm': "--with-stringm ${PIP_LOCK}",
    'misc': "-a ABPO,ADUMBRXNCOR,ROLLRXNCOR,CORSOL,CVELOCI,PINS,ENSEMBLE,SAMC,MCMA,GSBP,PIPF,POLAR,PNM,RISM,CONSPH,RUSH,TMD,DIMS,MSCALE,EDS ${PIP_LOCK}",
    'misc2': "--without-domdec --with-g09 -a DISTENE,MTS ${PIP_LOCK}",
    'tamd': "--without-mpi -a TAMD ${PIP_LOCK}",
    'mndo97': "--with-mndo97 ${PIP_LOCK}",
    'gamus': "--with-gamus ${PIP_LOCK}",
    'squantm': "--with-squantm ${PIP_LOCK}",
    'ljpme': "--with-ljpme ${PIP_LOCK}"
]

def charmmTests = [
    'openmm': 'cmake',
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
    'ljpme': 'M 2 X 2 cmake'
]

// Run a map of closures in batches of the given size
def runInBatches(Map jobs, int batchSize) {
    def jobList = jobs.collect { k, v -> [k, v] }
    for (int i = 0; i < jobList.size(); i += batchSize) {
        def batch = [:]
        def end = Math.min(i + batchSize, jobList.size())
        for (int j = i; j < end; j++) {
            batch[jobList[j][0]] = jobList[j][1]
        }
        parallel batch
    }
}

def ENV_SETUP = '''
    eval "$(/home/bucknerj/.local/bin/micromamba shell hook --shell zsh)"
    micromamba activate workshop
    export FFTW_HOME=$CONDA_PREFIX
'''

// Shell snippet to rotate test output: saves current output as old/
def TEST_ROTATE = '''
    if [[ -d output ]]; then
        rm -rf old
        mkdir old
        cp -r output* old/
        rm -rf output*
    fi
    if [[ -d old ]]; then
        for f in test.log compare.log diff.log test_results.xml; do
            if [[ -f $f ]]; then cp $f old/; rm $f; fi
        done
    fi
'''

pipeline {
    agent any
    options {
        timeout(time: 4, unit: 'HOURS')
        timestamps()
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'master', url: 'gitlab:/bucknerj/dev-release'
            }
        }
        stage('Checkout Scripts') {
            steps {
                dir('jenkins_scripts') {
                    git branch: 'main',
                        url: 'git@github-bucknerj:bucknerj/jenkins_scripts.git'
                }
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
                                    ${ENV_SETUP}
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
                    def buildJobs = [:]
                    charmmConfigs.each { name, configArgs ->
                        buildJobs["Build ${name}"] = {
                            stage("Build ${name}") {
                                echo "Building ${name}..."
                                sh """
                                    ${ENV_SETUP}
                                    pushd install-${name}
                                    nice -n 10 ninja -j ${BUILD_THREADS} -C build/cmake install
                                    popd
                                """
                                echo "...finished building ${name}"
                            }
                        }
                    }
                    runInBatches(buildJobs, MAX_BUILD_CONCURRENT)
                }
            }
        }
        stage("Test") {
            steps {
                script {
                    // GPU tests — run sequentially to avoid GPU memory contention
                    charmmTests.findAll { k, _ -> k in GPU_TESTS }.each { name, testArgs ->
                        stage("Test ${name} (GPU)") {
                            echo "Testing ${name} (GPU)..."
                            sh """
                                ${ENV_SETUP}
                                export CUDA_VISIBLE_DEVICES=0
                                pushd install-${name}/test
                                ${TEST_ROTATE}
                                nice -n 10 ./test.com ${testArgs} output old/output &> test.log
                                popd
                            """
                            echo "...finished testing ${name}"
                        }
                    }

                    // CPU tests — run in batches
                    def cpuTestJobs = [:]
                    charmmTests.findAll { k, _ -> !(k in GPU_TESTS) }.each { name, testArgs ->
                        cpuTestJobs["Test ${name}"] = {
                            stage("Test ${name}") {
                                echo "Testing ${name}..."
                                sh """
                                    ${ENV_SETUP}
                                    pushd install-${name}/test
                                    ${TEST_ROTATE}
                                    nice -n 10 ./test.com ${testArgs} output old/output &> test.log
                                    popd
                                """
                                echo "...finished testing ${name}"
                            }
                        }
                    }
                    runInBatches(cpuTestJobs, MAX_TEST_CONCURRENT)
                }
            }
        }
        stage("Pytest pyCHARMM") {
            steps {
                script {
                    echo "Running pyCHARMM pytest suite..."
                    sh """
                        ${ENV_SETUP}
                        pushd install-pycharmm
                        export CHARMM_DATA_DIR=\$(pwd)/toppar
                        cd tool/pycharmm
                        nice -n 10 pytest -v --tb=short --junitxml=pytest-results.xml tests/ 2>&1 | tee pytest.log
                        popd
                    """
                    junit 'install-pycharmm/tool/pycharmm/pytest-results.xml'
                    echo "...finished pyCHARMM pytest"
                }
            }
        }
        stage("Report") {
            steps {
                script {
                    def parallelJobs = [:]
                    charmmTests.each { name, testArgs ->
                        parallelJobs["Report ${name}"] = {
                            stage("Report ${name}") {
                                echo "Reporting ${name}..."
                                sh """
                                    ${ENV_SETUP}
                                    pushd install-${name}/test
                                    python ${WORKSPACE}/jenkins_scripts/grade-tests.py --tol 0.0001 > ${name}.xml
                                    popd
                                """
                                junit "install-${name}/test/${name}.xml"
                                echo "...finished reporting ${name}"
                            }
                        }
                    }
                    parallel parallelJobs
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'install-*/test/*.log,install-*/test/*.xml,install-pycharmm/tool/pycharmm/pytest*',
                             allowEmptyArchive: true
        }
        failure {
            echo 'Pipeline failed — check archived test logs for details'
        }
    }
}
