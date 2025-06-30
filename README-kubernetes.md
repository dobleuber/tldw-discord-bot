# TLDW Discord Bot - Kubernetes Deployment Guide

This guide explains how to deploy the TLDW Discord bot to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured to access your cluster
- Docker image built and available in a registry
- Discord bot token and Google API key

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t your-registry/tldw-discord-bot:latest .

# Push to registry
docker push your-registry/tldw-discord-bot:latest
```

### 2. Create Secrets

Create the required secrets with your actual values:

```bash
kubectl create secret generic tldw-secrets \
  --from-literal=discord-token="YOUR_DISCORD_TOKEN" \
  --from-literal=google-api-key="YOUR_GOOGLE_API_KEY" \
  --from-literal=redis-password="YOUR_REDIS_PASSWORD" \
  --namespace=tldw-bot
```

### 3. Update Image Reference

Edit `k8s/kustomization.yaml` to use your image:

```yaml
images:
- name: tldw-discord-bot
  newName: your-registry/tldw-discord-bot
  newTag: latest
```

### 4. Deploy

```bash
# Create namespace first
kubectl apply -f k8s/namespace.yaml

# Deploy all resources
kubectl apply -k k8s/

# Or deploy individual resources
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-service.yaml
kubectl apply -f k8s/redis-statefulset.yaml
kubectl apply -f k8s/bot-service.yaml
kubectl apply -f k8s/bot-deployment.yaml
```

## Architecture

### Components

- **Namespace**: `tldw-bot` - Isolates bot resources
- **Redis StatefulSet**: Persistent cache storage
- **Bot Deployment**: Discord bot application
- **Services**: Internal communication and health checks
- **ConfigMap**: Non-sensitive configuration
- **Secrets**: Tokens and API keys

### Networking

- Redis is accessible internally via `redis:6379`
- Bot health checks are available on port `8080`
- No external services are exposed by default

### Storage

- Redis uses a 1Gi PersistentVolume for data persistence
- Data persists across pod restarts and updates

## Configuration

### Environment Variables

Configuration is managed through ConfigMap and Secrets:

**ConfigMap (k8s/configmap.yaml):**
- `REDIS_HOST`: Redis service hostname
- `REDIS_PORT`: Redis port (6379)
- `CACHE_EXPIRATION_HOURS`: Cache TTL (24 hours)
- `MESSAGE_HISTORY_LIMIT`: Messages to search (5)
- `LOG_LEVEL`: Logging level (INFO)
- `LOG_FORMAT`: Logging format (json for K8s)

**Secrets (k8s/secrets.yaml):**
- `discord-token`: Discord bot authentication
- `google-api-key`: Google Gemini AI access
- `redis-password`: Redis authentication

### Resource Limits

**Bot Container:**
- Requests: 256Mi memory, 100m CPU
- Limits: 512Mi memory, 500m CPU

**Redis Container:**
- Requests: 128Mi memory, 100m CPU
- Limits: 256Mi memory, 200m CPU

## Health Checks

The bot includes comprehensive health monitoring:

### Liveness Probe
- Endpoint: `GET /health`
- Checks if the bot process is alive
- Initial delay: 30s, period: 30s

### Readiness Probe
- Endpoint: `GET /ready`
- Checks if the bot is ready to handle commands
- Initial delay: 10s, period: 5s

### Redis Health Check
- Command: `redis-cli -a $REDIS_PASSWORD ping`
- Initial delay: 30s, period: 10s

## Monitoring and Logging

### Structured Logging

The bot outputs JSON-formatted logs when `LOG_FORMAT=json`, making it compatible with Kubernetes logging infrastructure:

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "tldw.bot",
  "message": "Bot connected to Discord",
  "module": "bot",
  "function": "on_ready",
  "line": 42
}
```

### Viewing Logs

```bash
# Bot logs
kubectl logs -n tldw-bot deployment/tldw-bot -f

# Redis logs
kubectl logs -n tldw-bot statefulset/redis -f

# All logs
kubectl logs -n tldw-bot -l app.kubernetes.io/name=tldw-discord-bot -f
```

## Operations

### Scaling

The bot is designed to run as a single replica (Discord bots cannot be horizontally scaled):

```bash
# Bot scaling is not recommended
# Redis can only run 1 replica in this configuration
```

### Updates

Rolling updates are configured for zero-downtime deployments:

```bash
# Update image
kubectl set image deployment/tldw-bot tldw-bot=your-registry/tldw-discord-bot:new-tag -n tldw-bot

# Check rollout status
kubectl rollout status deployment/tldw-bot -n tldw-bot

# Rollback if needed
kubectl rollout undo deployment/tldw-bot -n tldw-bot
```

### Backup and Recovery

Redis data is persisted in a PersistentVolume. For production deployments, consider:

1. **Volume Snapshots**: Use your cloud provider's snapshot functionality
2. **Redis Backups**: Implement regular Redis dumps
3. **Multi-AZ Deployment**: Deploy across availability zones

## Troubleshooting

### Common Issues

**Pod Not Starting:**
```bash
# Check pod status
kubectl get pods -n tldw-bot

# Check events
kubectl describe pod <pod-name> -n tldw-bot

# Check logs
kubectl logs <pod-name> -n tldw-bot
```

**Health Check Failures:**
```bash
# Test health endpoints
kubectl port-forward -n tldw-bot deployment/tldw-bot 8080:8080
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

**Redis Connection Issues:**
```bash
# Check Redis status
kubectl exec -it -n tldw-bot statefulset/redis -- redis-cli -a $REDIS_PASSWORD ping

# Check Redis logs
kubectl logs -n tldw-bot statefulset/redis
```

**Secret Issues:**
```bash
# Verify secrets exist
kubectl get secrets -n tldw-bot

# Check secret values (base64 encoded)
kubectl get secret tldw-secrets -n tldw-bot -o yaml
```

### Debug Commands

```bash
# Get all resources
kubectl get all -n tldw-bot

# Describe deployment
kubectl describe deployment tldw-bot -n tldw-bot

# Check resource usage
kubectl top pods -n tldw-bot

# Execute commands in bot pod
kubectl exec -it -n tldw-bot deployment/tldw-bot -- /bin/bash
```

## Security Considerations

- Secrets are stored in Kubernetes Secrets (base64 encoded, not encrypted at rest by default)
- Consider using sealed-secrets, external-secrets, or similar tools for production
- Network policies can be added to restrict inter-pod communication
- Resource limits prevent resource exhaustion
- Non-root user is used in the container

## Production Recommendations

1. **Use a proper image registry** (not Docker Hub for production)
2. **Implement proper secret management** (Vault, AWS Secrets Manager, etc.)
3. **Set up monitoring** (Prometheus, Grafana)
4. **Configure log aggregation** (ELK stack, Fluentd)
5. **Use network policies** for security
6. **Implement backup strategies** for Redis data
7. **Configure resource quotas** and limits
8. **Use multiple availability zones**
9. **Set up alerting** for failures
10. **Regular security updates** for base images