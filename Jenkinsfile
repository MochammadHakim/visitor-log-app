// Server-local pipeline. Configure parameters and credentials before enabling webhook.
pipeline {
    agent any
    options { disableConcurrentBuilds(); timeout(time: 15, unit: 'MINUTES') }
    parameters {
        string(name: 'DEPLOY_DIR', defaultValue: '', description: 'Dedicated absolute directory on Docker host; no spaces')
        string(name: 'FRONTEND_URL', defaultValue: 'http://127.0.0.1:8090', description: 'Endpoint reachable from this agent')
    }
    environment { COMPOSE_PROJECT_NAME = 'uts-visitor-log' }
    triggers { githubPush() }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    if (!(params.DEPLOY_DIR ==~ /\/[A-Za-z0-9_\/-]+/) || params.DEPLOY_DIR == '/') {
                        error('Configure dedicated DEPLOY_DIR before deployment')
                    }
                    env.IMAGE_TAG = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                }
            }
        }
        stage('Syntax Check') {
            steps {
                sh 'python3 -m py_compile backend/app.py && python3 -m unittest discover -s tests -v'
                withCredentials([file(credentialsId: 'visitor-log-env', variable: 'APP_ENV')]) {
                    sh 'docker compose --env-file "$APP_ENV" config --quiet'
                }
            }
        }
        stage('Build Image') {
            steps {
                withCredentials([file(credentialsId: 'visitor-log-env', variable: 'APP_ENV')]) {
                    sh 'docker compose --env-file "$APP_ENV" build backend'
                }
            }
        }
        stage('Automated Deployment') {
            steps {
                withCredentials([file(credentialsId: 'visitor-log-env', variable: 'APP_ENV')]) {
                    sh '''set -eu
                        mkdir -p "$DEPLOY_DIR/frontend"
                        cp frontend/*.html frontend/*.js frontend/*.css frontend/nginx.conf "$DEPLOY_DIR/frontend/"
                        cp docker-compose.yml "$DEPLOY_DIR/"
                        docker compose --project-directory "$DEPLOY_DIR" --env-file "$APP_ENV" up -d --no-build
                    '''
                }
            }
        }
        stage('Health Check') {
            options { timeout(time: 60, unit: 'SECONDS') }
            steps {
                withCredentials([file(credentialsId: 'visitor-log-env', variable: 'APP_ENV')]) {
                    sh '''set -eu
                        for attempt in $(seq 1 12); do
                            if docker compose --project-directory "$DEPLOY_DIR" --env-file "$APP_ENV" exec -T backend python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=2)' >/dev/null && curl --fail --silent --max-time 2 "$FRONTEND_URL/login.html" >/dev/null && curl --fail --silent --max-time 2 "$FRONTEND_URL/api/health" >/dev/null; then exit 0; fi
                            sleep 2
                        done
                        exit 1
                    '''
                }
            }
        }
    }
}
