# Integrate with COS Lite

This guide explains how to deploy a local COS Lite (Canonical Observability Stack) environment and integrate it with your charmed Node.js application. This integration is crucial for enabling comprehensive monitoring and logging of your application within a Juju environment.

## Overview

COS Lite provides essential observability tools (like Prometheus for metrics and Loki for logs) that your charmed application can expose data to. For local development and testing, you will deploy a dedicated COS Lite instance within your MicroK8s environment and then establish relations with your application.

## Steps for Integration

### 1. Deploy COS Lite Environment Locally

First, ensure your MicroK8s environment is ready and then deploy the COS Lite bundle. This process is automated by the [scripts/deploy-cos-lite.sh](../../scripts/deploy-cos-lite.sh) script.

**Prerequisites from `host-setup.md` are assumed to be met.**

1.  **Enable necessary MicroK8s add-ons:**
    ```bash
    sudo microk8s enable dns
    sudo microk8s enable hostpath-storage
    # Determine your IP address for MetalLB configuration
    IPADDR=$(ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc')
    sudo microk8s enable metallb:$IPADDR-$IPADDR
    ```
2.  **Wait for MicroK8s components to be ready:**
    ```bash
    microk8s kubectl rollout status deployments/hostpath-provisioner -n kube-system -w
    microk8s kubectl rollout status deployments/coredns -n kube-system -w
    microk8s kubectl rollout status daemonset.apps/speaker -n metallb-system -w
    ```
3.  **Create a Juju model for COS Lite:** The `coslite.sh` script uses `cos` as the model name.
    ```bash
    if ! juju models | grep -q "cos"; then
        echo "Model 'cos' does not exist. Creating..."
        juju add-model "cos"
        echo "Model 'cos' created."
    else
        echo "Model 'cos' already exists."
    fi
    juju switch cos
    ```
4.  **Deploy the COS Lite bundle:** This will deploy the core COS Lite components like Prometheus, Loki, Grafana, and Alertmanager.
    ```bash
    curl -L https://raw.githubusercontent.com/canonical/cos-lite-bundle/main/overlays/offers-overlay.yaml -O
    curl -L https://raw.githubusercontent.com/canonical/cos-lite-bundle/main/overlays/storage-small-overlay.yaml -O
    juju deploy cos-lite \
            --trust \
            --overlay ./offers-overlay.yaml \
            --overlay ./storage-small-overlay.yaml
    ```

### 2. Deploy Your Application and Establish Relations

After COS Lite is deployed, you can deploy your charmed Node.js application and relate it to the COS Lite components for observability.

1.  **Switch to your application's Juju model (if different from `cos`):**
    ```bash
    juju switch nodejs
    ```
2.  **Deploy your application charm:** Ensure your application's charm and rock image are built and accessible.
    ```bash
    # Example: Replace <path-to-app-charm> with the actual path
    # and adjust resource name and image path as per your charm's definition.
    juju deploy nodejs-app ./<path-to-app-charm>.charm --resource app-image=localhost:32000/<rock-name>:<rock-version>
    ```
3.  **Deploy the Grafana Agent Charm:** This agent is crucial for collecting metrics and logs from your application.
    ```bash
    juju deploy grafana-agent-k8s --trust
    ```
4.  **Establish relations with COS Lite:** These commands connect your application's observability endpoints to the respective COS Lite services.
    ```bash
    juju relate nodejs-app admin/cos.grafana-dashboards
    juju relate nodejs-app:metrics-endpoint grafana-agent-k8s
    juju relate nodejs-app:logging grafana-agent-k8s
    juju relate grafana-agent-k8s cos.loki-logging
    juju relate grafana-agent-k8s cos.prometheus-receive-remote-write
    ```
    *Replace `nodejs-app`, `<rock-name>`, and `<rock-version>` with your actual application details.*

By following these steps, your Node.js application will be integrated with a locally deployed COS Lite stack, allowing you to monitor its performance and collect logs.

## Next Steps

With COS Lite integration complete, you may also want to:

* [Integrate with NGINX Ingress](./integrate-nginx-ingress.md) to expose your application's external access.