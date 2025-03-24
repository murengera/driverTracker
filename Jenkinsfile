pipeline {
    agent any

    environment {
        SONAR_TOKEN = credentials('token') // Store token in Jenkins credentials
    }

        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'sonar-scanner -Dsonar.projectKey=my_project -Dsonar.sources=. -Dsonar.host.url=http://localhost:9000 -Dsonar.login=$SONAR_TOKEN'
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
}
