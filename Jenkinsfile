pipeline {
    agent any

    environment {
        VENV_DIR = 'venv'
        GCP_PROJECT = "infra-window-453718-m0"
        IMAGE_NAME = "gcr.io/${GCP_PROJECT}/mlops-project1"
        CLUSTER_NAME = "autopilot-cluster-1"           // ← Change this to your GKE cluster name
        ZONE = "us-central1-a"                   // ← Change this to your cluster zone/region
        NAMESPACE = "default"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    stages {

        stage('Clone Repository') {
            steps {
                echo '📥 Cloning GitHub repository...'
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo '🐍 Setting up virtual environment...'
                sh '''
                    python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                '''
            }
        }

        stage('Build & Push Docker Image to GCR') {
            steps {
                withCredentials([file(credentialsId: 'gcp_key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    echo '🐳 Building and Pushing Docker Image to GCR...'
                    sh '''
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT}
                        gcloud auth configure-docker --quiet

                        docker build -t ${IMAGE_NAME}:latest .
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Deploy to GKE') {
            steps {
                withCredentials([file(credentialsId: 'gcp_key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    echo '🚀 Deploying to Google Kubernetes Engine (GKE)...'
                    sh '''
                        # Authenticate with GCP
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT}

                        # Get GKE cluster credentials
                        gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE}

                        # Apply Kubernetes manifests
                        kubectl apply -f k8s/deployment.yaml -n ${NAMESPACE}
                        kubectl apply -f k8s/service.yaml -n ${NAMESPACE}

                        # Update image in deployment
                        kubectl set image deployment/mlops-project1 \
                            mlops-project1=${IMAGE_NAME}:latest \
                            -n ${NAMESPACE}

                        # Check rollout status
                        kubectl rollout status deployment/mlops-project1 -n ${NAMESPACE}
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ Deployment to GKE completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed. Please check the logs above.'
        }
        always {
            echo '🧹 Cleaning up virtual environment...'
            sh 'rm -rf ${VENV_DIR}'
        }
    }
}