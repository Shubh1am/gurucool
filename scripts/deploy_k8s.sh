#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
K8S_DIR="$ROOT_DIR/k8s"
NAMESPACE="gharuka-guru"

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo ".env not found in $ROOT_DIR. Create one from .env.example and fill secrets." >&2
  exit 1
fi

echo "Applying Kubernetes resources to namespace $NAMESPACE"

# create namespace
kubectl apply -f "$K8S_DIR/namespace.yaml"

echo "Creating env secret from .env"
kubectl delete secret gharuka-guru-env -n $NAMESPACE --ignore-not-found || true
kubectl create secret generic gharuka-guru-env --from-env-file="$ROOT_DIR/.env" -n $NAMESPACE

echo "Creating regcred (Docker registry secret). Provide REGISTRY, REGISTRY_USERNAME, REGISTRY_PASSWORD in environment or export them before running this script."
if [ -z "${REGISTRY:-}" ] || [ -z "${REGISTRY_USERNAME:-}" ] || [ -z "${REGISTRY_PASSWORD:-}" ]; then
  echo "REGISTRY/REGISTRY_USERNAME/REGISTRY_PASSWORD environment variables are required to create regcred." >&2
  echo "You can create regcred manually with: kubectl create secret docker-registry regcred --docker-server=..." >&2
else
  kubectl delete secret regcred -n $NAMESPACE --ignore-not-found || true
  kubectl create secret docker-registry regcred \
    --docker-server="$REGISTRY" \
    --docker-username="$REGISTRY_USERNAME" \
    --docker-password="$REGISTRY_PASSWORD" \
    -n $NAMESPACE
fi

echo "Applying core manifests"
kubectl apply -f "$K8S_DIR/secret-env.yaml" -n $NAMESPACE
kubectl apply -f "$K8S_DIR/configmap.yaml" -n $NAMESPACE
kubectl apply -f "$K8S_DIR/postgres-statefulset.yaml" -n $NAMESPACE
kubectl apply -f "$K8S_DIR/backend-deployment.yaml" -n $NAMESPACE
kubectl apply -f "$K8S_DIR/backend-service.yaml" -n $NAMESPACE
kubectl apply -f "$K8S_DIR/ui-deployment.yaml" -n $NAMESPACE
kubectl apply -f "$K8S_DIR/ui-service.yaml" -n $NAMESPACE
kubectl apply -f "$K8S_DIR/ingress.yaml" -n $NAMESPACE

echo "Waiting for rollout status"
kubectl rollout status deployment/gharuka-guru-backend -n $NAMESPACE --timeout=120s || true
kubectl rollout status deployment/gharuka-guru-ui -n $NAMESPACE --timeout=120s || true
kubectl rollout status statefulset/postgresql -n $NAMESPACE --timeout=120s || true

echo "Deployment complete. Use 'kubectl get pods -n $NAMESPACE' to check pod status." 
