# SeederBot Development Progress

## Project Overview
Building a secure FastAPI service that triggers media searches from ChatGPT via webhook, using Jackett → Radarr/Sonarr → Deluge as the primary path, with torrent blackhole fallback.

## Current Status ✅

### Completed Stages
- ✅ **Stage 1**: Repo scaffolding, FastAPI skeleton, CI/CD setup
- ✅ **Stage 2**: Radarr integration implemented and tested
- ✅ **Infrastructure**: Radarr installed and running on seedbox

### What's Working
- FastAPI app with Bearer token authentication
- `/health` and `/grab` endpoints functional
- Radarr client with movie search, add, and system status methods
- 10 passing tests (pytest)
- Code quality tools configured (ruff, black, isort)
- GitHub Actions CI workflow
- Docker setup ready

## Current Configuration State

### Environment Variables Needed
```bash
# App Configuration
APP_TOKEN=your-secure-random-token-here
MODE=radarr
HOST=0.0.0.0
PORT=8000

# Radarr Configuration (PRIMARY PATH)
RADARR_URL=http://your-seedbox:port
RADARR_API_KEY=your-radarr-api-key-here
ROOT_FOLDER=/path/to/movies
QUALITY_PROFILE_ID=4

# Jackett Configuration (FALLBACK PATH - not yet implemented)
JACKETT_URL=http://your-seedbox:port
JACKETT_API_KEY=your-jackett-api-key
CATEGORIES=2000,2010
MIN_SEEDERS=20
QUALITY_REGEX=1080p.*WEB-DL|1080p.*BluRay
EXCLUDE_REGEX=CAM|TS|TC|WORKPRINT
MIN_SIZE_GB=2.5
MAX_SIZE_GB=6.0
AUTOADD_WATCH_DIR=/path/to/torrents/watch
```

### Current Setup
- **Seedbox**: Linux-based remote server with Deluge
- **Radarr**: Installed and running (web UI accessible)
- **Jackett**: Not yet installed
- **Deluge**: Running with AutoAdd capability

## Immediate Next Steps 🎯

### 1. Complete Radarr Configuration (5-10 mins)
```bash
# Access Radarr web UI
# Navigate to: Settings → General → Security
# Copy the API Key
# Update your local .env file:
RADARR_API_KEY=your-actual-api-key
RADARR_URL=http://your-actual-seedbox-url:port
```

### 2. Test Radarr Integration (2 mins)
```bash
# Start the API locally
poetry run uvicorn src.app.main:app --reload

# Test the integration
curl -X POST http://localhost:8000/grab \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"title": "Inception", "year": 2010}'
```

### 3. Radarr Initial Setup
- Set root folder path in Radarr UI
- Configure quality profiles (note the ID for .env)
- Will need Jackett later for indexers

## Pending Stages 🔄

### Stage 3: Jackett Blackhole Implementation
- Install Jackett on seedbox
- Implement `jackett.py` for Torznab API calls
- Implement `select.py` for result filtering
- Implement `blackhole.py` for .torrent file writing
- Add integration tests

### Stage 4: Docker & Compose
- Finalize Dockerfile (multi-stage build)
- Complete docker-compose.yml
- Add optional service examples
- Test containerized deployment

### Stage 5: Documentation & OpenAPI
- Complete README with setup instructions
- Add architecture diagrams
- Finalize ChatGPT Action OpenAPI spec
- Add troubleshooting guide

### Stage 6: GitHub Repository
- Create public repo on GitHub
- Push code with clean commit history
- Set up GitHub Actions
- Add repository documentation

### Stage 7: Polish & Production
- Add structured logging
- Implement health checks
- Add request validation
- Performance optimization

## Key Commands to Remember

### Development
```bash
# Start development server
make dev

# Run tests
make test

# Code quality
make lint
make format

# Docker
make docker-build
make docker-up
```

### Testing API
```bash
# Health check
curl http://localhost:8000/health

# Test grab (Radarr mode)
curl -X POST http://localhost:8000/grab \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"title": "Movie Title", "year": 2023}'
```

### Seedbox Management
```bash
# Check if Radarr is running
pgrep -laf Radarr

# Start Radarr (from seedbox)
cd ~/private/Radarr
screen -dmS Radarr /bin/bash -c 'export TMPDIR=~/.config/Radarr/tmp; ./Radarr -nobrowser'

# Get Radarr URL
echo "http://$(hostname -f):$(sed -rn 's|(.*)<Port>(.*)</Port>|\2|p' ~/.config/Radarr/config.xml)/"
```

## Architecture Overview

```
ChatGPT Action → SeederBot API → [Radarr Mode OR Blackhole Mode] → Deluge

Mode A (Primary): POST /grab → Radarr API → Jackett (via Radarr) → Deluge
Mode B (Fallback): POST /grab → Jackett API → Download .torrent → Watch Folder → Deluge AutoAdd
```

## Important Notes

### Security
- Bearer token authentication required
- No secrets in repository (use .env)
- HTTPS assumed at reverse proxy level
- Designed for personal use only

### Compliance
- Documentation emphasizes legal content only
- Tracker rules must be followed
- User responsible for ratio maintenance

### Quality Filters (Current Config)
- 1080p WEB-DL/BluRay preferred
- 2.5-6GB file size range
- 20+ seeders minimum
- Excludes CAM/TS/TC quality

## Troubleshooting

### Common Issues
- **Radarr not starting**: Check permissions, ensure TMPDIR is set
- **API timeouts**: Verify network connectivity between services
- **Quality profiles**: Note IDs from Radarr UI for configuration
- **File permissions**: Ensure Deluge can read blackhole directory

### Debug Commands
```bash
# Check Radarr logs
tail -f ~/.config/Radarr/logs/radarr.txt

# Test Radarr API directly
curl -H "X-Api-Key: your-key" http://your-radarr:port/api/v3/system/status

# Check app logs
poetry run uvicorn src.app.main:app --log-level debug
```

## Project Structure
```
seederbot/
├── src/app/           # FastAPI application
├── tests/             # Test suite
├── ops/               # Docker, compose, nginx configs
├── .github/workflows/ # CI/CD
├── .env.example       # Environment template
└── CLAUDE.md         # This file
```

## When Resuming Development

1. **Read this file completely**
2. **Check current environment state** (what's running, what's configured)
3. **Update .env** with real credentials
4. **Run tests** to verify current state
5. **Continue from "Immediate Next Steps"** section
6. **Update this file** as progress is made

## Estimated Time to Completion
- **Stage 3** (Jackett blackhole): 2-3 hours
- **Stage 4** (Docker): 1 hour
- **Stage 5** (Documentation): 1 hour
- **Stage 6** (GitHub): 30 minutes
- **Stage 7** (Polish): 1-2 hours

**Total remaining**: ~6-8 hours of development time