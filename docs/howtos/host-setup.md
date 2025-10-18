# Host Setup for Charmed Applications

This guide provides step-by-step instructions to prepare your host for developing and deploying charmed applications, following the principles of 12-factor app charming. This setup enables you to run and test your charm locally before deploying it to larger environments.

## LXD Installation

LXD is essential for creating and managing lightweight system containers that mimic a local cloud environment, where your charmed application will run.
It is required for building a rock. Below are the steps to get it running:
```sh
sudo snap install lxd
lxd --version
sudo lxd init --auto
getent group lxd | grep -qwF "$USER" || sudo usermod -aG lxd "$USER"
newgrp lxd
```

## Docker Installation (try to avoid)

If possible, avoid installing Docker on the same host as LXD, as it can lead to [network connectivity issues]((https://documentation.ubuntu.com/lxd/latest/howto/network_bridge_firewalld/#prevent-connectivity-issues-with-lxd-and-docker)). For testing purposes, if you must install Docker:
```sh
sudo snap install docker
sudo addgroup --system docker
sudo adduser $USER docker
newgrp docker

sudo snap disable docker
sudo snap enable docker
```

## Rockcraft Install

Rockcraft is used to build OCI-compliant image resources (called "rocks") for your application. These images encapsulate your application's dependencies and runtime environment.
```sh
sudo snap install rockcraft --channel latest/edge --classic
rockcraft --version
```

## Charmcraft Install

Charmcraft is the command-line tool for initializing, packaging, and publishing charms. It allows you to build the operator logic around your application's rock.
```sh
sudo snap install charmcraft --channel latest/edge --classic
charmcraft --version
```

## Enable experimental extensions

As the expressjs-framework extensions for Rockcraft and Charmcraft are still in development, we must enable experimental extensions for each:

```sh
export ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true
export CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true
```

## MicroK8s Install

MicroK8s provides a lightweight, local Kubernetes environment, which is required to deploy and test your Kubernetes charms locally using Juju.
```sh
sudo snap install microk8s --channel 1.31-strict/stable
sudo adduser $USER snap_microk8s
newgrp snap_microk8s
```
Several MicroK8s add-ons are required or deployment:
```sh
# Required for Juju to provide storage volumes
sudo microk8s enable hostpath-storage
# Required to host the OCI image of the application
sudo microk8s enable registry
# Required to expose the application
sudo microk8s enable ingress
```

Check the status of MicroK8s to make sure it is ready:
```sh
sudo microk8s status --wait-ready
```
If successful, the terminal will output microk8s is running along with a list of enabled and disabled add-ons.

## Juju Install

Juju is the open-source orchestration engine that deploys, integrates, and manages your charmed applications across various infrastructures. It coordinates the local cloud (LXD/MicroK8s) and runs your charm. It is required to deploy the application.  
_Hint: Use the same version of Juju as your target environment to be on the safe side._
```sh
sudo snap install juju --channel 3.6/stable
mkdir -p ~/.local/share
juju bootstrap microk8s dev
```
It could take a few minutes to download the images.

if you followed step by step until here, 'controller' is the only juju model and we are switching to that. 
```sh
juju switch controller 
juju status --color --relations
```
Don't use this model for anything if you don't know what you are doing.

## Next Steps

After successfully setting up your host environment, you can now proceed to:

* [Set up your Development Environment](./development-setup.md) to start coding.
* [Pack and Deploy the Charm](./pack-and-deploy.md) to get your application running in Juju.