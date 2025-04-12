

pipeline {
    agent any

    environment {
        SCANNER_HOME = "/home/daltonbigirimana/Downloads/sonar-scanner-7.0.2.4839-linux-x64"
        DOCKER_IMAGE = 'daltonbigirimana5/triptrackerimage'
        TAG = "${BUILD_NUMBER}"
        RENDER_SERVICE_ID = 'srv-cvgm73dds78s73f824dg'  // Replace with actual Render service ID
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Checkout from SCM') {
            steps {
                git branch: 'main',credentialsId:github, url: 'https://github.com/murengera/triptracker.git'  // Updated repo URL
            }
        }
//
//         stage("SonarQube Analysis") {
//             steps {
//                 withSonarQubeEnv('sonar-server') {
//                     withCredentials([string(credentialsId: 'Sonar-token', variable: 'SONAR_TOKEN')]) {
//                         sh """
//                             ${SCANNER_HOME}/bin/sonar-scanner \
//                             -Dsonar.projectName=triptracker \
//                             -Dsonar.projectKey=triptracker \
//                             -Dsonar.host.url=http://localhost:9000 \
//                             -Dsonar.token=${SONAR_TOKEN} \
//                             -X  # Debug logging enabled
//                         """
//                     }
//                 }
//             }
//         }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${DOCKER_IMAGE}:${TAG} -t ${DOCKER_IMAGE}:latest .'
            }
        }

        stage('Test') {
            steps {
                sh 'docker run --rm ${DOCKER_IMAGE}:${TAG} python manage.py test'
            }
        }

        stage("TRIVY Security Scan") {
            steps {
                sh "trivy image ${DOCKER_IMAGE}:latest > trivyimage.txt"
                archiveArtifacts artifacts: 'trivyimage.txt', fingerprint: true
            }
        }

        stage('Push to Registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'f166e43a-d338-4020-88f9-5b3e6fe4e091', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh '''
                        echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
                        docker push ${DOCKER_IMAGE}:${TAG}
                        docker push ${DOCKER_IMAGE}:latest
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

        stage('Deploy to Container') {
            steps {
                sh 'docker stop triptracker || true && docker rm triptracker || true'
                sh 'docker run -d --name triptracker -p 8000:8000 ${DOCKER_IMAGE}:latest'
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
