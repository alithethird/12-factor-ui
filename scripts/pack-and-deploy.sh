#!/bin/bash
set -euo pipefail

# Source common variables
source scripts/common-vars.sh

# Update version in rockcraft.yaml and charm.py
sed -i "s/^version: \".*\"/version: \"${APP_VERSION}\"/" rockcraft.yaml
sed -i "s/self.unit.set_workload_version(\".*\")/self.unit.set_workload_version(\"${APP_VERSION}\")/" charm/src/charm.py

clear
echo "============================================================"
echo "== Packing Rock ============================================"
echo "============================================================"
echo "Model Name:   ### ${APP_MODEL_NAME} ###"
echo "App Name:     ### ${APP_NAME} ###"
echo "App Version:  ### ${APP_VERSION} ###"
echo "Charm Name:   ### ${CHARM_NAME} ###"
echo "Rock Name:    ### ${ROCK_NAME} ###"

export ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=True 

rockcraft clean
rockcraft pack


echo
echo
echo "============================================================"
echo "== Uploading Rock to Registry =============================="
echo "============================================================"
rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false oci-archive:${ROCK_NAME}_${APP_VERSION}_${ARCH_NAME}.rock docker://localhost:32000/${ROCK_NAME}:${APP_VERSION}


echo
echo
echo "============================================================"
echo "== Packing Charm ==========================================="
echo "============================================================"

export CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=True 

cd charm
charmcraft clean
charmcraft fetch-libs
charmcraft pack
cd ..

echo
echo
echo "============================================================"
echo "== Deploying / Refreshing Application ======================"
echo "============================================================"

if ! juju models | grep -q "${APP_MODEL_NAME}"; then
    echo "Model '${APP_MODEL_NAME}' does not exist. Creating..."
    juju add-model "${APP_MODEL_NAME}"
    echo "Model '${APP_MODEL_NAME}' created."
else
    echo "Model '${APP_MODEL_NAME}' already exists."
fi

juju switch ${APP_MODEL_NAME}

echo "Setting model constraint arch=${ARCH_NAME}"
juju set-model-constraints -m "${APP_MODEL_NAME}" arch="${ARCH_NAME}"

if juju status --color --relations | grep -q "^${APP_NAME}\\s"; then
  echo "Application '${APP_NAME}' exists. Running juju refresh..."
  juju refresh ${APP_NAME} --path ./charm/${CHARM_NAME}_${ARCH_NAME}.charm --resource app-image=localhost:32000/${ROCK_NAME}:${APP_VERSION}
else
  echo "Application '${APP_NAME}' does not exist. Running juju deploy..."
  juju deploy ./charm/${CHARM_NAME}_${ARCH_NAME}.charm ${APP_NAME} --resource app-image=localhost:32000/${ROCK_NAME}:${APP_VERSION}
fi