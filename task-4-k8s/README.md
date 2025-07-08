 # Task 4: Kubernetes Pod Scaling (K8s + HPA)

This project demonstrates automatic, resource-based scaling of a containerized application using Kubernetes and the Horizontal Pod Autoscaler (HPA).

## Architecture Overview

The system consists of a simple FastAPI application designed to be CPU-intensive on demand, deployed to a local Kubernetes cluster (Minikube).

- **The Application (`cpu-loader-app`):** A Python FastAPI server with two endpoints:
  - `/`: A root endpoint to confirm the service is running.
  - `/load`: An endpoint that performs a CPU-intensive calculation (a large loop of square roots) to simulate high load.
- **Docker Image:** The application is containerized using a standard Python Dockerfile.
- **Kubernetes Deployment (`deployment.yaml`):** This manifest tells Kubernetes to run our application. Critically, it defines **resource requests** (`requests: cpu: "200m"`). This request is essential, as it provides a baseline for the HPA to calculate CPU utilization percentage.
- **Kubernetes Service (`service.yaml`):** This manifest exposes the Deployment via a stable network endpoint. It uses the `NodePort` type, which makes it easy to access the service from outside the Minikube cluster for testing.
- **Horizontal Pod Autoscaler (`hpa.yaml`):** This manifest defines the autoscaling logic. It is configured to monitor the `cpu-loader-deployment` and maintain an average CPU utilization of 50% across all pods. If the average usage exceeds 50% of the requested `200m`, the HPA will create new pods, up to a maximum of 10. If the load subsides, it will scale back down to a minimum of 1.

## Environment Setup

### Prerequisites

- Docker
- Minikube
- `kubectl`

## How to Run

1.  **Start Minikube:** Initialize your local Kubernetes cluster.

    ```bash
    minikube start
    ```

2.  **Enable Metrics Server:** The HPA requires the metrics-server addon to function.

    ```bash
    minikube addons enable metrics-server
    ```

3.  **Point Docker to Minikube's Registry:** This crucial step allows you to build a Docker image that is immediately available to your Minikube cluster without needing a remote registry.

    ```bash
    eval $(minikube -p minikube docker-env)
    ```
    *(Note: You may need to run this command in each new terminal you use for this task).*

4.  **Build the Application Image:** From the `task-4-k8s/` directory, build the image.

    ```bash
    docker build -t cpu-loader-app:latest .
    ```

5.  **Deploy to Kubernetes:** Apply all the Kubernetes manifest files.

    ```bash
    kubectl apply -f deployment.yaml
    kubectl apply -f service.yaml
    kubectl apply -f hpa.yaml
    ```

## How to Test Autoscaling

1.  **Monitor Pods (Terminal 1):** Open a terminal and watch the pod status and CPU usage. The `-w` flag will "watch" for changes.

    ```bash
    kubectl get pods -w
    # In another terminal, watch the CPU usage:
    watch kubectl top pods
    ```

2.  **Expose the Service (Terminal 2):** Open a new terminal and create a tunnel to the service running inside Minikube. This command will print a URL (e.g., `http://127.0.0.1:xxxxx`).

    ```bash
    minikube service cpu-loader-service
    ```

3.  **Generate Load (Terminal 3):** Using the URL from the previous step, run an infinite loop of `curl` requests to the `/load` endpoint.

    ```bash
    # Replace the URL with the one from your `minikube service` output
    while true; do curl http://127.0.0.1:xxxxx/load; done
    ```

4.  **Observe Scaling Up:** In your monitoring terminal, you will see the CPU usage of the initial pod spike. After a minute, Kubernetes will begin creating new pods to handle the load. You can check the HPA's status with `kubectl get hpa`.

5.  **Observe Scaling Down:** Stop the `curl` loop by pressing `CTRL+C` in Terminal 3. After a few minutes of low CPU usage, you will see the extra pods being terminated until only one remains.
