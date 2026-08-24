# GitHub Repository Secrets Guide

This file lists the repository secrets required by the CI/CD workflow (`.github/workflows/deploy.yml`) for building images and deploying to your self-hosted Kubernetes cluster.

Required secrets:

- `REGISTRY` — The container registry hostname (e.g., `docker.io` or `123456789012.dkr.ecr.us-east-1.amazonaws.com`).
- `REGISTRY_USERNAME` — Username for the registry (for Docker Hub this is your Docker ID; for ECR use an access key or use GitHub OIDC).
- `REGISTRY_PASSWORD` — Password or token for the registry (for ECR you can use an IAM user access key or configure OIDC flow).
- `IMAGE_NAMESPACE` — Your image namespace (e.g., `yourorg` or Docker Hub username). Used to tag images: `${{ secrets.REGISTRY }}/${{ secrets.IMAGE_NAMESPACE }}/...`.
- `KUBE_CONFIG_DATA` — Base64-encoded kubeconfig for your target cluster. Example:

```
cat ~/.kube/config | base64 | pbcopy
# then paste into the GitHub secret value
```

Optional / notes:
- For AWS ECR, consider using GitHub's `aws-actions/configure-aws-credentials` and `amazon-ecr/docker-login` to avoid storing long-lived secrets.
- If using GHCR, set `REGISTRY=ghcr.io` and use a GitHub personal access token with `write:packages`.
- Keep `KUBE_CONFIG_DATA` restricted (only allow workflows from protected branches to run deploy steps).

How the workflow uses these secrets:
- `REGISTRY`, `REGISTRY_USERNAME`, and `REGISTRY_PASSWORD` are used to authenticate and push images.
- `IMAGE_NAMESPACE` defines the image path.
- `KUBE_CONFIG_DATA` is decoded into a temporary `kubeconfig` file used by `kubectl` to apply manifests.
