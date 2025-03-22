pipeline {
    agent any  // Run the pipeline on any agent with Docker and Python installed

    environment {
        // Define the virtual environment path
        VENV = 'venv'
    }

    stages {
        // Stage 1: Checkout the source code from version control
        stage('Checkout') {
            steps {
                checkout scm  // Automatically checks out the code from the configured SCM (e.g., Git)
            }
        }

        // Stage 2: Set up Python environment and install dependencies
        stage('Set up Python environment') {
            steps {
                script {
                    // Create the virtual environment
                    sh 'python3 -m venv ${VENV}'  // Create a virtual environment

                    // Install dependencies from requirements.txt directly
                    sh './${VENV}/bin/pip install -r requirements.txt'  // Install dependencies
                }
            }
        }

        // Stage 3: Install pytest and run tests using pytest-django to generate the XML report
        stage('Run tests') {
            steps {
                script {
                    // Install pytest and pytest-django if not already installed
                    sh './${VENV}/bin/pip install pytest pytest-django'

                    // Run tests using pytest and generate the JUnit XML report
                    sh './${VENV}/bin/pytest --maxfail=1 --disable-warnings -q --junitxml=test-results.xml'
                }
            }
        }
    }

    post {
        always {
            // Publish test results to Jenkins
            junit '**/test-results.xml'  // Ensure this matches the path of the generated XML report
        }
    }
}
