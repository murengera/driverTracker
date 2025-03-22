pipeline {
    // Use a Docker agent with Python 3.8 to ensure a consistent environment
    agent {
        docker {
            image 'python:3.8'
        }
    }

    // Define the stages of the pipeline
    stages {
        // Stage 1: Checkout the source code from version control
        stage('Checkout') {
            steps {
                checkout scm  // Automatically checks out the code from the configured SCM (e.g., Git)
            }
        }

        // Stage 2: Install project dependencies
        stage('Install dependencies') {
            steps {
                sh 'pip install -r requirements.txt'  // Installs dependencies listed in requirements.txt
            }
        }

        // Stage 3: Run the tests
        stage('Run tests') {
            steps {
                sh 'pytest --junitxml=test-results.xml'  // Runs tests with pytest and generates a JUnit XML report
            }
        }
    }

    // Post-build actions
    post {
        always {
            junit 'test-results.xml'  // Publishes test results in Jenkins, even if tests fail
        }
    }
}