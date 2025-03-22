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


    post {
        always {
            // Publish test results to Jenkins, assuming test-results.xml is the generated file
            junit '**/test-results.xml'  // Ensure this matches the path of the generated XML report
        }
    }
}
