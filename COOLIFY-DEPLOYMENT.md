# Coolify Deployment Guide for Archon

This guide covers deploying Archon using Coolify, a self-hosted deployment platform that simplifies Docker container management.

## Prerequisites

1. **Coolify instance** running and accessible
2. **GitHub Container Registry access** (images are private by default)
3. **Supabase project** with database configured
4. **Domain name** for your Archon instance

## Quick Start

### 1. Prepare Your Repository

Ensure your repository has:
- `docker-compose.coolify.yaml` (already created)
- Published Docker images in GitHub Container Registry
- Environment variables configured

### 2. Create Application in Coolify

1. **Login to Coolify** and navigate to your project
2. **Click "New Application"**
3. **Select "Docker Compose"** as the deployment method
4. **Upload `docker-compose.coolify.yaml`** file

### 3. Configure Environment Variables

In Coolify's environment variables section, set these **required** variables:

```bash
# Required - GitHub Container Registry
GITHUB_USERNAME=yourusername
IMAGE_TAG=latest

# Required - Domain configuration
DOMAIN=your-domain.com

# Required - Database configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Optional - AI features
OPENAI_API_KEY=sk-your-openai-key-here
AGENTS_ENABLED=false

# Optional - Observability
LOGFIRE_TOKEN=your-logfire-token-here
LOG_LEVEL=INFO
```

### 4. Deploy

1. **Review configuration** in Coolify
2. **Click "Deploy"**
3. **Monitor deployment** in the logs section

## Coolify-Specific Features

### Automatic HTTPS

Coolify automatically handles SSL certificates via Let's Encrypt:
- **HTTP to HTTPS redirect** configured via Traefik
- **Automatic certificate renewal**
- **Secure headers** applied automatically

### Traefik Integration

The compose file includes Traefik labels for:
- **Automatic routing** based on domain and path
- **Load balancing** across service instances
- **Path prefix stripping** for API routes
- **Priority routing** (frontend gets priority)

### Service Routing

- **Frontend**: `https://your-domain.com/` → archon-frontend:3737
- **API**: `https://your-domain.com/api/*` → archon-server:8181
- **MCP**: `https://your-domain.com/mcp/*` → archon-mcp:8051
- **Agents**: `https://your-domain.com/agents/*` → archon-agents:8052

## Deployment Options

### Basic Deployment (Core Services)

Deploy with default configuration:
- Server, MCP, and Frontend services
- Automatic HTTPS via Traefik
- Health checks and monitoring

### With AI Agents

To enable AI agents service:

1. **Set environment variable**:
   ```bash
   AGENTS_ENABLED=true
   ```

2. **Enable agents profile** in Coolify:
   - Go to application settings
   - Add `agents` to the profiles list
   - Redeploy

### Custom Domain Configuration

1. **Set your domain**:
   ```bash
   DOMAIN=your-custom-domain.com
   ```

2. **Configure DNS**:
   - Point your domain to Coolify's IP
   - Or use Coolify's subdomain feature

3. **Redeploy** to apply changes

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_USERNAME` | Your GitHub username | `yourusername` |
| `DOMAIN` | Your domain name | `archon.yourdomain.com` |
| `SUPABASE_URL` | Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | `eyJ...` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `IMAGE_TAG` | Docker image tag | `latest` | `v1.0.0` |
| `OPENAI_API_KEY` | OpenAI API key | - | `sk-...` |
| `AGENTS_ENABLED` | Enable AI agents | `false` | `true` |
| `LOGFIRE_TOKEN` | Logfire token | - | `your-token` |
| `LOG_LEVEL` | Log level | `INFO` | `DEBUG` |

## Monitoring and Management

### Health Checks

All services include health checks:
- **Server**: `/health` endpoint
- **MCP**: Socket connection test
- **Agents**: `/health` endpoint
- **Frontend**: HTTP response check

### Logs

Access logs in Coolify:
1. **Go to your application**
2. **Click "Logs" tab**
3. **Select service** to view specific logs
4. **Use filters** to search logs

### Resource Monitoring

Coolify provides:
- **CPU and memory usage** graphs
- **Container status** monitoring
- **Automatic restarts** on failure
- **Resource limits** enforcement

## Troubleshooting

### Common Issues

#### 1. Image Pull Failures

**Problem**: Cannot pull images from GitHub Container Registry

**Solution**:
```bash
# Ensure images are published
# Check GitHub Actions workflow completed successfully
# Verify GITHUB_USERNAME is correct
```

#### 2. Domain Not Accessible

**Problem**: Application not accessible via domain

**Solution**:
- Check DNS configuration
- Verify domain is set correctly in environment variables
- Check Traefik routing in Coolify logs

#### 3. Database Connection Issues

**Problem**: Services can't connect to Supabase

**Solution**:
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check Supabase project is active
- Review service logs for connection errors

#### 4. Services Not Starting

**Problem**: Services fail to start or restart frequently

**Solution**:
- Check resource limits in Coolify
- Review health check configuration
- Check environment variables are set correctly

### Debugging Steps

1. **Check service logs** in Coolify
2. **Verify environment variables** are set
3. **Test health endpoints** manually
4. **Check resource usage** in Coolify dashboard
5. **Review Traefik routing** configuration

## Advanced Configuration

### Custom Resource Limits

Modify resource limits in `docker-compose.coolify.yaml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4G      # Increase for high load
      cpus: '2.0'     # Increase for CPU-intensive tasks
```

### Multiple Environments

Create separate applications in Coolify for:
- **Development**: `archon-dev`
- **Staging**: `archon-staging`
- **Production**: `archon-prod`

Use different:
- Domains (`dev.yourdomain.com`, `staging.yourdomain.com`)
- Image tags (`dev`, `staging`, `latest`)
- Environment variables

### Backup and Recovery

Coolify provides:
- **Automatic backups** of application configurations
- **Environment variable** backup and restore
- **Container state** monitoring
- **Rollback capabilities**

## Security Considerations

### Environment Variables

- **Never expose** sensitive variables in logs
- **Use Coolify's** secure environment variable storage
- **Rotate keys** regularly
- **Limit access** to Coolify instance

### Network Security

- **HTTPS only** (automatically configured)
- **Traefik security headers** (automatically applied)
- **Container isolation** via Docker networks
- **Resource limits** to prevent resource exhaustion

### Access Control

- **Secure Coolify instance** with strong authentication
- **Limit user access** to necessary applications
- **Monitor access logs** regularly
- **Use VPN** for Coolify access if possible

## Support

For issues:

1. **Check Coolify logs** first
2. **Review this guide** for common solutions
3. **Check GitHub issues** for known problems
4. **Create new issue** with Coolify logs and configuration details

## Migration from Other Platforms

### From Docker Compose

1. **Export environment variables** from existing setup
2. **Update image references** to use GitHub Container Registry
3. **Remove port mappings** (handled by Traefik)
4. **Add Coolify labels** (already included)

### From Kubernetes

1. **Convert services** to Docker Compose format
2. **Replace Ingress** with Traefik labels
3. **Convert ConfigMaps** to environment variables
4. **Update health checks** format
