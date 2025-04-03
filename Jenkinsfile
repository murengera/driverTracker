//
//
// pipeline {
//     agent any
//
//     environment {
//         DOCKER_IMAGE = 'daltonbigirimana5/dockerimages'
//         TAG = "${BUILD_NUMBER}"
//         RENDER_SERVICE_ID = 'srv-cvgm73dds78s73f824dg'  // Replace with your actual Render service ID
//     }
//
//     stages {
//         stage('Checkout') {
//             steps {
//                 git branch: 'main',
//                     url: 'https://github.com/murengera/driverTracker.git'  // Replace with your repo URL
//             }
//         }
//
//         stage('Build Docker Image') {
//             steps {
//                 sh 'docker build -t ${DOCKER_IMAGE}:${TAG} -t ${DOCKER_IMAGE}:production .'
//             }
//         }
//
//         stage('Test') {
//             steps {
//                 sh 'docker run --rm ${DOCKER_IMAGE}:${TAG} python manage.py test'
//             }
//         }
//
//         stage('Push to Registry') {
//             steps {
//                 withCredentials([usernamePassword(credentialsId: 'f166e43a-d338-4020-88f9-5b3e6fe4e091', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
//                     sh '''
//                         echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
//                         docker push ${DOCKER_IMAGE}:${TAG}
//                         docker push ${DOCKER_IMAGE}:production
//                     '''
//                 }
//             }
//         }
//
//         stage('Deploy to Render') {
//             steps {
//                 withCredentials([string(credentialsId: 'render-api-token', variable: 'RENDER_API_TOKEN')]) {
//                     sh """
//                         curl -X POST \
//                           -H "Authorization: Bearer ${RENDER_API_TOKEN}" \
//                           -H "Content-Type: application/json" \
//                           -d '{"dockerImage": "${DOCKER_IMAGE}:${TAG}"}' \
//                           https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys
//                     """
//                 }
//             }
//         }
//     }
// }



pipeline {
    agent any

    tools {
        jdk 'jdk17'
        nodejs 'node16'
    }

    environment {
        SCANNER_HOME = "/home/daltonbigirimana/Downloads/sonar-scanner-7.0.2.4839-linux-x64"
        DOCKER_IMAGE = 'daltonbigirimana5/triptrackerimage'
        TAG = "${BUILD_NUMBER}"
        RENDER_SERVICE_ID = 'srv-cvgm73dds78s73f824dg'  // Replace with your actual Render service ID
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/murengera/driverTracker.git'  // Replace with your repo URL
            }
        }

        stage("SonarQube Analysis") {
            steps {
                withSonarQubeEnv('sonar-server') {
                    withCredentials([string(credentialsId: 'Sonar-token', variable: 'SONAR_TOKEN')]) {
                        sh """
                            ${SCANNER_HOME}/bin/sonar-scanner \
                            -Dsonar.projectName=driverTracker \
                            -Dsonar.projectKey=driverTracker \
                            -Dsonar.host.url=http://localhost:9000 \
                            -Dsonar.token=${SONAR_TOKEN}
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${DOCKER_IMAGE}:${TAG} -t ${DOCKER_IMAGE}:production .'
            }
        }

        stage('Test') {
            steps {
                sh 'docker run --rm ${DOCKER_IMAGE}:${TAG} python manage.py test'
            }
        }

        stage('Push to Registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'f166e43a-d338-4020-88f9-5b3e6fe4e091', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh '''
                        echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
                        docker push ${DOCKER_IMAGE}:${TAG}
                        docker push ${DOCKER_IMAGE}:production
                    '''
                }
            }
        }

        stage('Deploy to Render') {
            steps {
                withCredentials([string(credentialsId: 'render-api-token', variable: 'RENDER_API_TOKEN')]) {
                    sh """
                        curl -X POST \
                          -H "Authorization: Bearer ${RENDER_API_TOKEN}" \
                          -H "Content-Type: application/json" \
                          -d '{"dockerImage": "${DOCKER_IMAGE}:${TAG}"}' \
                          https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys
                    """
                }
            }
        }
    }

    post {
        always {
            emailext attachLog: true,
                subject: "'${currentBuild.result}'",
                body: "Project: ${env.JOB_NAME}<br/>" +
                      "Build Number: ${env.BUILD_NUMBER}<br/>" +
                      "URL: ${env.BUILD_URL}<br/>",
                to: 'postbox.aj99@gmail.com, daltonigirimana5@gmail.com'
        }
    }
}
