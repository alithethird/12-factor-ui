#!/bin/bash
set -euo pipefail

# Source common variables
source scripts/common-vars.sh

# Specific model name for COS Lite deployment
COS_MODEL_NAME="cos" # COS Lite is typically deployed in its own 'cos' model

# IP address for MetalLB, specific to this script
IPADDR=$(ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc')

clear
echo "COS Model Name: ### ${COS_MODEL_NAME} ###"
echo "App Name: ### ${APP_NAME} ###"
echo "Charm Name: ### ${CHARM_NAME} ###"
echo "Rock Name: ### ${ROCK_NAME} ###"
echo "Rock Version: ### ${APP_VERSION} ###"
echo "IP Address: ### ${IPADDR} ###"

sudo microk8s enable dns
sudo microk8s enable hostpath-storage
sudo microk8s enable metallb:${IPADDR}-${IPADDR}

microk8s kubectl rollout status deployments/hostpath-provisioner -n kube-system -w
microk8s kubectl rollout status deployments/coredns -n kube-system -w
microk8s kubectl rollout status daemonset.apps/speaker -n metallb-system -w

if ! juju models | grep -q "${COS_MODEL_NAME}"; then
    echo "Model '${COS_MODEL_NAME}' does not exist. Creating..."
    juju add-model "${COS_MODEL_NAME}"
    echo "Model '${COS_MODEL_NAME}' created."
else
    echo "Model '${COS_MODEL_NAME}' already exists."
fi

juju switch ${COS_MODEL_NAME}

curl -L https://raw.githubusercontent.com/canonical/charms.canonical.com/master/builds/bundles/cos-lite-k8s/bundle.yaml > cos-lite-k8s.yaml
juju deploy ./cos-lite-k8s.yaml --trust

juju deploy grafana-agent-k8s --channel stable --trust

juju wait -v -m ${COS_MODEL_NAME} --timeout 30m

# Deploy the application charm and relate to COS Lite
# Note: This part of the script assumes the application charm is deployed
# to the COS model, which might not be typical for applications.
# It's usually integrated cross-model or if the app is in the same model.
# The [integrate-cos-lite.md](./howtos/integrate-cos-lite.md) guide handles cross-model integration more broadly.
juju deploy ./<path-to-your-app-charm>.charm --resource app-image=localhost:32000/${ROCK_NAME}:${APP_VERSION}
juju relate ${APP_NAME} grafana-agent-k8s:juju-info
juju relate ${APP_NAME} prometheus:metrics
juju relate ${APP_NAME} loki:logging