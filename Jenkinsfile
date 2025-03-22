pipeline {
    // Run the pipeline on any agent with Docker installed
    agent any

    stages {
        // Stage 1: Checkout the source code from version control
        stage('Checkout') {
            steps {
                checkout scm  // Automatically checks out the code from the configured SCM (e.g., Git)
            }
        }

        // Stage 2: Install project dependencies inside a Python container
        stage('Install dependencies') {
            steps {
                script {
                    docker.image('python:3.8').inside('-v $HOME/.cache/pip:/root/.cache/pip') {
                        sh 'pip install -r requirements.txt'  // Install dependencies
                    }
                }
            }
        }

        // Stage 3: Run tests inside a Python container
        stage('Run tests') {
            steps {
                script {
                    docker.image('python:3.8').inside('-v $HOME/.cache/pip:/root/.cache/pip') {
                        sh 'pytest --junitxml=test-results.xml'  // Run tests and generate a JUnit XML report
                    }
                }
            }
        }

        // Stage 4: Build the Docker image for the DRF application
        stage('Build Docker image') {
            steps {
                script {
                    docker.build('tripplanner')  // Build the Docker image using the Dockerfile in the repo root
                }
            }
        }

        // Stage 5: Run a Docker container to verify it starts
        stage('Run Docker container') {
            steps {
                script {
                    // Start the container in detached mode and capture the container ID
                    def containerId = sh(script: 'docker run -dtripplanner', returnStdout: true).trim()
                    sleep 10  // Wait 10 seconds for the container to start

                    // Check if the container is still running
                    def status = sh(script: "docker inspect -f '{{.State.Running}}' ${containerId}", returnStdout: true).trim()
                    if (status != 'true') {
                        error "Container is not running"  // Fail the pipeline if the container isn't running
                    }

                    // Clean up: stop and remove the container
                    sh "docker stop ${containerId}"
                    sh "docker rm ${containerId}"
                }
            }
        }
    }

    // Post-build actions
    post {
        always {
            junit 'test-results.xml'  // Publish test results in Jenkins
        }
    }
}
