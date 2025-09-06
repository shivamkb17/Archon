# Production Deployment Guide

This guide covers deploying Archon to production using the pre-built Docker images from GitHub Container Registry.

## Prerequisites

1. **Docker and Docker Compose** installed on your server
2. **GitHub Container Registry access** (images are private by default)
3. **Supabase project** with database configured
4. **Domain name** (optional, for SSL/HTTPS)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/archon.git
cd archon

# Copy environment template
cp env.example .env
```

### 2. Configure Environment

Edit `.env` file with your production values:

```bash
# Required - Get from Supabase dashboard
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Optional - AI features
OPENAI_API_KEY=sk-your-openai-key-here

# Production settings
GITHUB_USERNAME=yourusername
IMAGE_TAG=latest  # or specific version like v1.0.0
LOG_LEVEL=INFO
PROD=true
AGENTS_ENABLED=false  # Set to true if you want AI agents

# Ports (adjust if needed)
ARCHON_SERVER_PORT=8181
ARCHON_MCP_PORT=8051
ARCHON_AGENTS_PORT=8052
ARCHON_UI_PORT=3737
HOST=your-domain.com  # or localhost for testing
```

### 3. Login to GitHub Container Registry

```bash
# Login with your GitHub token
echo $GITHUB_TOKEN | docker login ghcr.io -u yourusername --password-stdin

# Or use your GitHub password (less secure)
docker login ghcr.io -u yourusername
```

### 4. Deploy

```bash
# Basic deployment (server, MCP, frontend)
docker-compose -f docker-compose-prod.yml up -d

# With AI agents enabled
docker-compose -f docker-compose-prod.yml --profile agents up -d

# With Nginx reverse proxy
docker-compose -f docker-compose-prod.yml --profile nginx up -d
```

## Deployment Options

### Option 1: Basic Deployment (No Reverse Proxy)

```bash
docker-compose -f docker-compose-prod.yml up -d
```

**Access:**
- Frontend: `http://your-server:3737`
- API: `http://your-server:8181`
- MCP: `http://your-server:8051`

### Option 2: With Nginx Reverse Proxy

```bash
docker-compose -f docker-compose-prod.yml --profile nginx up -d
```

**Access:**
- Frontend: `http://your-server` (port 80)
- API: `http://your-server/api`
- MCP: `http://your-server/mcp`

### Option 3: With SSL/HTTPS

1. **Obtain SSL certificates** (Let's Encrypt recommended)
2. **Place certificates** in `./ssl/` directory:
   ```
   ssl/
   ├── cert.pem
   └── key.pem
   ```
3. **Update nginx.conf** - uncomment HTTPS server block
4. **Deploy with nginx**:
   ```bash
   docker-compose -f docker-compose-prod.yml --profile nginx up -d
   ```

## Service Management

### View Logs

```bash
# All services
docker-compose -f docker-compose-prod.yml logs -f

# Specific service
docker-compose -f docker-compose-prod.yml logs -f archon-server
```

### Update Services

```bash
# Pull latest images
docker-compose -f docker-compose-prod.yml pull

# Restart with new images
docker-compose -f docker-compose-prod.yml up -d
```

### Scale Services

```bash
# Scale server instances (if needed)
docker-compose -f docker-compose-prod.yml up -d --scale archon-server=2
```

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose-prod.yml down

# Stop and remove volumes
docker-compose -f docker-compose-prod.yml down -v
```

## Monitoring and Health Checks

### Health Check Endpoints

- **Server**: `http://your-server:8181/health`
- **MCP**: `http://your-server:8051/health`
- **Agents**: `http://your-server:8052/health`
- **Frontend**: `http://your-server:3737`
- **Nginx**: `http://your-server/health`

### Resource Monitoring

```bash
# View resource usage
docker stats

# View service status
docker-compose -f docker-compose-prod.yml ps
```

## Security Considerations

### 1. Environment Variables

- **Never commit** `.env` file to version control
- **Use strong passwords** for all services
- **Rotate API keys** regularly
- **Limit file permissions**: `chmod 600 .env`

### 2. Network Security

- **Use HTTPS** in production
- **Configure firewall** to only allow necessary ports
- **Use reverse proxy** (Nginx) for additional security
- **Enable rate limiting** (configured in nginx.conf)

### 3. Container Security

- **Regular updates**: Pull latest images regularly
- **Resource limits**: Configured in docker-compose-prod.yml
- **Read-only volumes**: Docker socket mounted read-only
- **Health checks**: All services have health monitoring

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

```bash
# Re-login to GitHub Container Registry
docker logout ghcr.io
docker login ghcr.io -u yourusername
```

#### 2. Port Conflicts

```bash
# Check what's using the ports
sudo netstat -tulpn | grep :8181
sudo netstat -tulpn | grep :3737

# Change ports in .env file if needed
ARCHON_SERVER_PORT=9181
ARCHON_UI_PORT=4737
```

#### 3. Database Connection Issues

```bash
# Verify Supabase credentials
curl -H "apikey: $SUPABASE_SERVICE_KEY" $SUPABASE_URL/rest/v1/

# Check service logs
docker-compose -f docker-compose-prod.yml logs archon-server
```

#### 4. Out of Memory

```bash
# Check system resources
free -h
df -h

# Adjust resource limits in docker-compose-prod.yml
# Or scale down services
docker-compose -f docker-compose-prod.yml down
```

### Log Analysis

```bash
# Search for errors
docker-compose -f docker-compose-prod.yml logs | grep -i error

# Follow specific service logs
docker-compose -f docker-compose-prod.yml logs -f --tail=100 archon-server
```

## Backup and Recovery

### Database Backup

```bash
# Backup Supabase data (use Supabase dashboard or CLI)
# Or export via API if needed
```

### Configuration Backup

```bash
# Backup your configuration
tar -czf archon-config-backup.tar.gz .env docker-compose-prod.yml nginx.conf
```

## Performance Tuning

### 1. Resource Allocation

Adjust resource limits in `docker-compose-prod.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4G      # Increase for high load
      cpus: '2.0'     # Increase for CPU-intensive tasks
```

### 2. Nginx Optimization

- **Enable gzip** (already configured)
- **Adjust worker processes** in nginx.conf
- **Configure caching** for static assets

### 3. Database Optimization

- **Index optimization** in Supabase
- **Connection pooling** (configured in services)
- **Query optimization** in application code

## Support

For issues and questions:

1. **Check logs** first: `docker-compose -f docker-compose-prod.yml logs`
2. **Review this guide** for common solutions
3. **Check GitHub issues** for known problems
4. **Create new issue** with logs and configuration details
