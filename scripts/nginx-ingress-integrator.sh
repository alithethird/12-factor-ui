#!/bin/bash
set -euo pipefail

# Source common variables
source scripts/common-vars.sh

juju deploy nginx-ingress-integrator --channel=latest/stable --trust
juju integrate nginx-ingress-integrator ${APP_NAME}
juju config nginx-ingress-integrator service-hostname=${APP_NAME} path-routes=/
curl http://${APP_NAME} --resolve ${APP_NAME}:80:127.0.0.1