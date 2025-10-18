#!/bin/bash
set -euo pipefail

# Common variables for Node.js Charm Boilerplate scripts

# Source of truth for application version (read from 'version' file)
APP_VERSION=$(cat version)

# Application's primary Juju model name
APP_MODEL_NAME="nodejs"

# Application name within Juju
APP_NAME="nodejs-app"

# Rock image name, extracted from rockcraft.yaml
ROCK_NAME=$(grep '^name:' "rockcraft.yaml" | cut -d':' -f2 | xargs)

# Charm name, extracted from charm/charmcraft.yaml
CHARM_NAME=$(grep '^name:' "charm/charmcraft.yaml" | cut -d':' -f2 | xargs)

# Architecture of the build/deployment host (e.g., amd64)
ARCH_NAME=$(dpkg --print-architecture)

# Export variables so they are available in subshells and sourced scripts
export APP_VERSION
export APP_MODEL_NAME
export APP_NAME
export ROCK_NAME
export CHARM_NAME
export ARCH_NAME