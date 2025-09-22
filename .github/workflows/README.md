# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the Archon project.

## Docker Image Publishing

The `publish-docker.yml` workflow automatically builds and publishes Docker images for all Archon services to GitHub Container Registry (ghcr.io).

### Services Built

- **archon-server**: Main FastAPI server (port 8181)
- **archon-mcp**: MCP server (port 8051) 
- **archon-agents**: AI agents service (port 8052)
- **archon-frontend**: React frontend (port 3737)

### Triggers

The workflow runs on:
- Push to `main`, `master`, or `develop` branches
- Tag creation (e.g., `v1.0.0`)
- Pull requests to main branches
- Manual dispatch via GitHub UI

### Image Tags

Images are tagged with:
- `latest` - for main/master branch
- `develop` - for develop branch
- `pr-123` - for pull requests
- `v1.0.0` - for version tags
- `1.0` - for major.minor tags

### Registry Location

Images are published to: `ghcr.io/{owner}/archon-{service}:{tag}`

Example: `ghcr.io/yourusername/archon-server:latest`

### Usage

#### Pull and Run Individual Services

```bash
# Pull the latest images
docker pull ghcr.io/yourusername/archon-server:latest
docker pull ghcr.io/yourusername/archon-mcp:latest
docker pull ghcr.io/yourusername/archon-agents:latest
docker pull ghcr.io/yourusername/archon-frontend:latest

# Run with docker-compose (recommended)
# Copy env.example to .env and configure
cp env.example .env
# Edit .env with your Supabase credentials
docker-compose up -d
```

#### Using Specific Versions

```bash
# Use a specific version
docker pull ghcr.io/yourusername/archon-server:v1.0.0
docker pull ghcr.io/yourusername/archon-mcp:v1.0.0
```

### Security Features

- **Multi-architecture builds**: Supports both AMD64 and ARM64
- **Vulnerability scanning**: Uses Trivy to scan for security issues
- **Cache optimization**: Uses GitHub Actions cache for faster builds
- **Private registry**: Images are private by default (can be made public)

### Environment Variables

Required environment variables for running the containers:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Optional
OPENAI_API_KEY=sk-your-key-here
LOGFIRE_TOKEN=your-token-here
LOG_LEVEL=INFO
AGENTS_ENABLED=false
```

### Local Development

For local development, use the existing docker-compose setup:

```bash
# Start all services
docker-compose up -d

# Start with agents enabled
docker-compose --profile agents up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Troubleshooting

#### Authentication Issues

If you get authentication errors when pulling images:

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u yourusername --password-stdin
```

#### Build Failures

Check the Actions tab in your GitHub repository for detailed build logs. Common issues:

1. **Missing environment variables**: Ensure all required env vars are set
2. **Dockerfile issues**: Check Dockerfile syntax and dependencies
3. **Resource limits**: GitHub Actions has memory/CPU limits

#### Registry Permissions

To make images public (optional):

1. Go to your repository on GitHub
2. Click on "Packages" tab
3. Select the package
4. Go to "Package settings"
5. Change visibility to "Public"
