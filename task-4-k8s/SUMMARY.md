 
# Task 4 Summary: Kubernetes Pod Scaling

This document describes the challenges, key decisions, and potential improvements for the Kubernetes HPA task.

## Challenges Faced

1.  **Manifest Syntax Errors:** Initial attempts to apply the `hpa.yaml` manifest failed due to a missing `kind: HorizontalPodAutoscaler` field. This was a simple typo but highlights the strict, declarative nature of Kubernetes manifests and the importance of validation.

2.  **Local Image Registry:** A common challenge when working with local Kubernetes clusters like Minikube is making locally built Docker images available to the cluster. Pushing to a public registry like Docker Hub for every change is inefficient. This was solved by using the `eval $(minikube docker-env)` command, which configures the local Docker client to communicate directly with the Docker daemon inside the Minikube node.

## Architectural Decisions

1.  **CPU Utilization as a Scaling Metric:** CPU was chosen as the scaling metric because it is a universal and easily understandable indicator of load for compute-bound tasks. The HPA was configured to target 50% utilization, a common starting point that provides a good balance between resource usage and having enough headroom to handle sudden spikes in traffic before new pods are ready.

2.  **Defining Resource Requests and Limits:** The most critical decision for making the HPA work was defining `resources.requests.cpu` in the `Deployment` manifest. Without a defined request, the concept of "CPU utilization percentage" is meaningless to Kubernetes. Setting a request tells the HPA what "100%" capacity is for a single pod. A `limit` was also set as a safety measure to prevent a misbehaving pod from consuming all CPU on the node and causing system instability.

3.  **`imagePullPolicy: Never`:** This policy was chosen specifically for the local Minikube development environment. It tells Kubernetes *not* to try to pull the image from a remote registry and to use the one that already exists inside the Minikube node's local Docker daemon (which we built in the previous step). This would be changed to `Always` or `IfNotPresent` in a real production environment using a remote image registry.

4.  **`Service` Type `NodePort`:** The `NodePort` service type is ideal for quick testing and exposing an application from Minikube. It's simpler than setting up an Ingress controller for a basic demo. `minikube service` provides a convenient CLI command to automatically create a tunnel to this `NodePort`.

## Scope for Improvement

1.  **Custom Metrics for Scaling:** While CPU is a good general metric, it's often not the best indicator of application load. For example, an I/O-bound application's CPU might be low even when it's struggling. A more advanced solution would be to scale on custom metrics, such as:
    - **Requests per second (RPS):** Using an Ingress controller and Prometheus, we could scale based on the number of incoming requests.
    - **Queue Length:** For an application processing jobs from a queue (like in Task 3), we could scale based on the number of messages in the Kafka or RabbitMQ topic. This is a very common and effective pattern.

2.  **Liveness and Readiness Probes:** The current Deployment lacks liveness and readiness probes.
    - A **readiness probe** would tell the Service not to send traffic to a new pod until the application inside is fully initialized (e.g., has a database connection).
    - A **liveness probe** would tell Kubernetes to restart a pod if the application has crashed or become unresponsive.

3.  **Using an Ingress Controller:** For a more production-like setup, an Ingress controller (like NGINX or Traefik) should be used instead of a `NodePort` service. This would provide a single entry point for all services in the cluster, with proper host-based routing (e.g., `api.myapp.com`), SSL termination, and more advanced load-balancing features.

4.  **CI/CD Automation:** The current process of building and deploying is manual. A CI/CD pipeline (e.g., using GitHub Actions) would automate the entire process: on a push to the `main` branch, the pipeline would automatically build the Docker image, push it to a registry, and update the Kubernetes Deployment to use the new image tag.