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
                    docker.image('python:3.12').inside('-v $HOME/.cache/pip:/root/.cache/pip') {
                        sh 'pip install -r requirements.txt'  // Install dependencies
                    }
                }
            }
        }

        // Stage 3: Run tests inside a Python container
        stage('Run tests') {
            steps {
                script {
                    docker.image('python:3.12').inside('-v $HOME/.cache/pip:/root/.cache/pip') {
                        sh 'pytest --junitxml=test-results.xml'  // Run tests and generate a JUnit XML report
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