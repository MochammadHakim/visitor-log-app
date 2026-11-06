// Trusted VM agent only: Docker socket access grants host-level authority.
pipeline {
 agent any
 options { disableConcurrentBuilds(); skipDefaultCheckout(true); timeout(time: 15, unit: 'MINUTES') }
 stages {
  stage('Checkout') { steps { checkout scm } }
  stage('Syntax Check') { steps { sh 'sh ci/pipeline.sh validate' } }
  stage('Build Image') { steps { sh 'sh ci/pipeline.sh build' } }
  stage('Automated Deployment') { steps { sh 'sh ci/pipeline.sh deploy' } }
  stage('Health Check') {
   steps { sh 'sh ci/pipeline.sh health' }
   post { always { archiveArtifacts artifacts: 'evidence/health.json', allowEmptyArchive: false } }
  }
 }
}
