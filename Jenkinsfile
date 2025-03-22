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

                    // Install dependencies from requirements.txt without upgrading pip
                    sh './${VENV}/bin/pip install --upgrade setuptools'  // Optionally upgrade setuptools
                    sh './${VENV}/bin/pip install -r requirements.txt'  // Install dependencies
                }
            }
        }

        // Stage 3: Run Django tests using pytest
        stage('Run tests') {
            steps {
                script {
                    // Run Django tests inside the virtual environment
                    sh './${VENV}/bin/python manage.py test'  // Run Django's test suite

                    // Alternatively, use pytest if you have pytest-django installed
                    // sh './${VENV}/bin/pytest --maxfail=1 --disable-warnings -q'  // Run tests using pytest
                }
            }
        }
    }

    post {
        always {
            // Publish test results to Jenkins, if using pytest
            junit '**/test-*.xml'  // If you are using pytest with --junitxml=test-results.xml
        }
