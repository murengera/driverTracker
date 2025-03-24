pipeline {
    agent any

    environment {
        DOCKER_IMAGE = daltonbigirimana5/dockerimages'  // Replace with your Docker Hub username and app name
        TAG = "${BUILD_NUMBER}"           // Use Jenkins build number for versioning
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/murengera/driverTracker.git'  // Replace with your repo URL
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${DOCKER_IMAGE}:${TAG} .'
            }
        }

        stage('Test') {
            steps {
                sh 'docker run ${DOCKER_IMAGE}:${TAG} python manage.py test'
            }
        }

        stage('Push to Registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh 'docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD'
                    sh 'docker push ${DOCKER_IMAGE}:${TAG}'
                }
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([
                    string(credentialsId: 'database-url', variable: 'DATABASE_URL'),
                    string(credentialsId: 'secret-key', variable: 'SECRET_KEY')
                ]) {
                    sshagent(['server-ssh-credentials']) {
                        sh '''
                            ssh user@server << EOF
                            docker pull ${DOCKER_IMAGE}:${TAG}
                            docker stop daltonbigirimana5/dockerimages || true
                            docker rm daltonbigirimana5/dockerimages || true
                            docker run -d --name daltonbigirimana5/dockerimages -p 8000:8000 \
                                -e DATABASE_URL=${DATABASE_URL} \
                                -e SECRET_KEY=${SECRET_KEY} \
                                ${DOCKER_IMAGE}:${TAG}
                            EOF
                        '''
                    }
                }
            }
        }
    }
}