# Integrate with NGINX Ingress

This guide explains how to deploy and integrate the NGINX Ingress Integrator charm with your Node.js application to expose it via a public hostname. These steps are automated in the [scripts/nginx-ingress-integrator.sh](../../scripts/nginx-ingress-integrator.sh) script.

## Overview

The NGINX Ingress Integrator charm simplifies exposing your application by handling ingress configurations. This guide will walk you through deploying the integrator, relating it to your application, configuring its hostname, and verifying access.

## Prerequisites
* Your application should be deployed to a Juju model (e.g., `nodejs`).
* You have a running MicroK8s environment with the Ingress add-on enabled, as typically set up in [Host Setup](./host-setup.md).

## Steps

### 1. Deploy NGINX Ingress Integrator

First, deploy the `nginx-ingress-integrator` charm to your Juju model.

```bash
# Ensure you are in the correct Juju model, e.g., nodejs
juju switch nodejs

juju deploy nginx-ingress-integrator --channel=latest/stable --trust
```

### 2. Integrate with Your Application

Next, relate the NGINX Ingress Integrator to your Node.js application.

```bash
juju integrate nginx-ingress-integrator nodejs-app
```

### 3. Configure Ingress Hostname

Configure the `nginx-ingress-integrator` to expose your application via a specific hostname. For local testing, we'll use the application name as the hostname.

```bash
juju config nginx-ingress-integrator service-hostname=nodejs-app path-routes=/
```

### 4. Verify Access

After deployment and configuration, you can test access to your application using `curl`. Note that for `curl` to resolve the hostname locally, you might need to manually add an entry to your `/etc/hosts` file or use the `--resolve` flag as shown below.

```bash
curl http://nodejs-app --resolve nodejs-app:80:127.0.0.1
```
This command attempts to access your application via the configured hostname `nodejs-app` on `localhost:80`.

By following these steps, your Node.js application will be accessible via NGINX Ingress.

## Next Steps

You have successfully deployed and exposed your charmed Node.js application. You can now continue exploring other aspects of the boilerplate or refer back to the main documentation for more guides and explanations.

* [Return to Documentation Home](../../docs/index.md)
