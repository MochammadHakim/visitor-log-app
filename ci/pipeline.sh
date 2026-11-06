#!/bin/sh
# VM-specific paths; do not print resolved Compose configuration or private .env.
set -eu
export IMAGE_TAG="$(git rev-parse HEAD)"
export FRONTEND_BIND=172.20.100.100 FRONTEND_PORT=8090
host=/home/ubuntu/cloud-computing
# Test/build parsing needs placeholders only, never production credentials.
compose_build() {
 AUTH_USERNAME=validation AUTH_SALT=validation AUTH_PASSWORD_HASH=validation \
 docker compose --env-file /dev/null -f docker-compose.yml "$@"
}
helper() {
 docker run --rm --network host --volumes-from visitor-log-jenkins \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$host:$host" \
  -v /usr/bin/docker:/usr/local/bin/docker:ro \
  -v /usr/libexec/docker/cli-plugins/docker-compose:/usr/local/lib/docker/cli-plugins/docker-compose:ro \
  -e IMAGE_TAG -e FRONTEND_BIND -e FRONTEND_PORT -w "$WORKSPACE" python:3.12-slim "$@"
}
case "${1:-}" in
 validate)
  docker run --rm --volumes-from visitor-log-jenkins -w "$WORKSPACE" python:3.12-slim \
   sh -ec 'python -m py_compile backend/app.py ci/*.py; python -m unittest discover -s tests -v'
  compose_build config --quiet
  ;;
 build) compose_build build backend ;;
 deploy)
  helper python ci/stage_deploy.py "$host/deployment"
  helper docker compose -p uts-visitor-log -f "$host/deployment/docker-compose.yml" \
   --env-file "$host/.env" config --quiet
  # Recreate frontend as well: bind-mounted nginx.conf changes require a reload.
  helper docker compose -p uts-visitor-log -f "$host/deployment/docker-compose.yml" \
   --env-file "$host/.env" up -d --no-build --force-recreate
  ;;
 health) helper timeout 58 python ci/health_check.py ;;
 *) printf '%s\n' 'Usage: pipeline.sh validate|build|deploy|health' >&2; exit 2 ;;
esac
