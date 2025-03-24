// pipeline {
//     agent any
//
//     environment {
//         DOCKER_IMAGE = 'daltonbigirimana5/dockerimages'  // ✅ Fixed: Wrapped in quotes
//         TAG = "${BUILD_NUMBER}"  // Use Jenkins build number for versioning
//     }
//
//     stages {
//         stage('Checkout') {
//             steps {
//                git branch: 'main',
//                     url: 'https://github.com/murengera/driverTracker.git'  // Replace with your repo URL
//             }
//         }
//
//         stage('Build Docker Image') {
//             steps {
//                 sh 'docker build -t ${DOCKER_IMAGE}:${TAG} .'
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
//                     '''
//                 }
//             }
//         }
//
//
//                 }
//             }
//         }
//     }
// }
pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'daltonbigirimana5/dockerimages'
        TAG = "${BUILD_NUMBER}"
        RENDER_SERVICE_ID = 'srv-cvgm73dds78s73f824dg'  // Replace with your actual Render service ID
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/murengera/driverTracker.git'
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
                          https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys
                    """
                }
            }
        }
    }
}